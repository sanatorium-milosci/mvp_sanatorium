"""Testy kalkulatora cen oraz endpointów REST API."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from packages.api.app import app
from packages.api.kalkulator_ceny import oblicz_szacowany_koszt
from packages.api.zaleznosci import pobierz_repozytorium
from packages.core.models import (
    JednostkaCeny,
    Oferta,
    ProfilLeczniczy,
    Udogodnienia,
    Wyzywienie,
    Zrodlo,
)
from packages.storage.baza import BazaDanych
from packages.storage.repozytorium import RepozytoriumOfert


def test_kalkulator_ceny():
    # Turnus osoba: koszt jest dokładnie ceną
    assert oblicz_szacowany_koszt("1290.00", "turnus_osoba") == "1290.00"

    # Osobodoba ze znaną liczbą dni
    assert oblicz_szacowany_koszt("200.00", "osobodoba", liczba_dni=7) == "1400.00"

    # Osobodoba ze znaną liczbą nocy
    assert oblicz_szacowany_koszt("150.00", "osobodoba", liczba_nocy=10) == "1500.00"

    # Osobodoba ze znanym zakresem dat
    assert (
        oblicz_szacowany_koszt(
            "100.00",
            "osobodoba",
            termin_od=date(2026, 10, 1),
            termin_do=date(2026, 10, 11),
        )
        == "1000.00"
    )

    # Osobodoba bez dni i bez terminu: nie zgadujemy!
    assert oblicz_szacowany_koszt("200.00", "osobodoba") is None

    # Pokój doba: nie zgadujemy kosztu za osobę
    assert oblicz_szacowany_koszt("300.00", "pokoj_doba", liczba_dni=7) is None

    # Brak ceny
    assert oblicz_szacowany_koszt(None, "turnus_osoba") is None


@pytest.fixture
def klient_testowy() -> TestClient:
    baza = BazaDanych(":memory:")
    repo = RepozytoriumOfert(baza)

    oferta1 = Oferta(
        adapter="demo",
        zrodlo_id="pobyt-14",
        osrodek_klucz="demo-ustron",
        osrodek_nazwa="Sanatorium Ustroń",
        miejscowosc="Ustroń",
        nazwa_pakietu="Pakiet Kuracyjny 14 dni",
        liczba_dni=14,
        liczba_nocy=13,
        termin_od=date(2026, 10, 1),
        termin_do=date(2026, 10, 15),
        dostepny=True,
        cena=Decimal("2800.00"),
        jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
        wyzywienie=Wyzywienie.FB,
        profile=[ProfilLeczniczy.KARDIOLOGICZNY],
        udogodnienia=Udogodnienia(basen=True, winda=True),
        zrodlo=Zrodlo(
            url="https://example.com/1",
            pobrano_o=datetime.now(UTC),
            adapter="demo",
            wersja_adaptera="0.1.0",
            hash_tresci="1" * 64,
        ),
    )

    oferta2 = Oferta(
        adapter="demo",
        zrodlo_id="pobyt-7",
        osrodek_klucz="demo-kolobrzeg",
        osrodek_nazwa="Sanatorium Bałtyk",
        miejscowosc="Kołobrzeg",
        nazwa_pakietu="Tydzień nad morzem",
        liczba_dni=7,
        liczba_nocy=6,
        termin_od=date(2026, 11, 1),
        termin_do=date(2026, 11, 8),
        dostepny=False,
        cena=Decimal("200.00"),
        jednostka_ceny=JednostkaCeny.OSOBODOBA,
        wyzywienie=Wyzywienie.HB,
        profile=[ProfilLeczniczy.GORNE_DROGI_ODDECHOWE],
        udogodnienia=Udogodnienia(basen=False, winda=True),
        zrodlo=Zrodlo(
            url="https://example.com/2",
            pobrano_o=datetime.now(UTC),
            adapter="demo",
            wersja_adaptera="0.1.0",
            hash_tresci="2" * 64,
        ),
    )

    oferta_przeszla = Oferta(
        adapter="demo",
        zrodlo_id="pobyt-przeszly",
        osrodek_klucz="demo-ustron",
        osrodek_nazwa="Sanatorium Ustroń",
        miejscowosc="Ustroń",
        nazwa_pakietu="Turnus z zeszłego roku",
        liczba_dni=7,
        termin_od=date(2020, 1, 1),
        termin_do=date(2020, 1, 8),
        dostepny=True,
        cena=Decimal("999.00"),
        jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
        zrodlo=Zrodlo(
            url="https://example.com/past",
            pobrano_o=datetime.now(UTC),
            adapter="demo",
            wersja_adaptera="0.1.0",
            hash_tresci="3" * 64,
        ),
    )

    repo.upsert_oferty("demo", [oferta1, oferta2, oferta_przeszla])

    app.dependency_overrides[pobierz_repozytorium] = lambda: repo
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_api_zdrowie(klient_testowy: TestClient):
    odp = klient_testowy.get("/api/v1/zdrowie")
    assert odp.status_code == 200
    dane = odp.json()
    assert dane["status"] == "ok"
    assert dane["baza_ok"] is True
    assert dane["aktywne_oferty"] == 3

    # Alias /healthz
    odp_alias = klient_testowy.get("/healthz")
    assert odp_alias.status_code == 200
    assert odp_alias.json()["status"] == "ok"


def test_api_lista_ofert_i_filtry(klient_testowy: TestClient):
    # Domyślnie przeszłe turnusy są ukryte (razem == 2)
    odp = klient_testowy.get("/api/v1/oferty")
    assert odp.status_code == 200
    dane = odp.json()
    assert dane["stronicowanie"]["razem"] == 2
    assert len(dane["elementy"]) == 2

    # Z flagą pokaz_przeszle=true widoczne są 3 oferty
    odp_all = klient_testowy.get("/api/v1/oferty?pokaz_przeszle=true")
    assert odp_all.status_code == 200
    assert odp_all.json()["stronicowanie"]["razem"] == 3
    assert len(dane["elementy"]) == 2

    # Sprawdzenie kalkulacji kosztu całkowitego
    el_ustron = next(e for e in dane["elementy"] if e["osrodek"]["miejscowosc"] == "Ustroń")
    assert el_ustron["cena"]["szacowany_koszt_calkowity"] == "2800.00"

    el_kolobrzeg = next(e for e in dane["elementy"] if e["osrodek"]["miejscowosc"] == "Kołobrzeg")
    # 200.00 * 7 dni = 1400.00
    assert el_kolobrzeg["cena"]["szacowany_koszt_calkowity"] == "1400.00"

    # Filtr po miejscowości
    odp_miejsc = klient_testowy.get("/api/v1/oferty?miejscowosc=Ustroń")
    assert odp_miejsc.json()["stronicowanie"]["razem"] == 1

    # Filtr po basenie
    odp_basen = klient_testowy.get("/api/v1/oferty?basen=true")
    assert odp_basen.json()["stronicowanie"]["razem"] == 1
    assert odp_basen.json()["elementy"][0]["osrodek"]["miejscowosc"] == "Ustroń"

    # Tylko dostępne
    odp_dost = klient_testowy.get("/api/v1/oferty?tylko_dostepne=true")
    assert odp_dost.json()["stronicowanie"]["razem"] == 1

    # Błędny zakres dat (termin_do < termin_od)
    odp_bad_date = klient_testowy.get("/api/v1/oferty?termin_od=2026-12-01&termin_do=2026-11-01")
    assert odp_bad_date.status_code == 400


def test_api_szczegoly_oferty(klient_testowy: TestClient):
    lista = klient_testowy.get("/api/v1/oferty").json()["elementy"]
    pierwsze_id = lista[0]["id"]

    odp = klient_testowy.get(f"/api/v1/oferty/{pierwsze_id}")
    assert odp.status_code == 200
    assert odp.json()["id"] == pierwsze_id

    odp_404 = klient_testowy.get("/api/v1/oferty/999999")
    assert odp_404.status_code == 404


def test_api_filtry_metadane(klient_testowy: TestClient):
    odp = klient_testowy.get("/api/v1/filtry")
    assert odp.status_code == 200
    dane = odp.json()
    assert "Ustroń" in dane["miejscowosci"]
    assert "Kołobrzeg" in dane["miejscowosci"]
    assert dane["liczba_ofert_razem"] == 3
