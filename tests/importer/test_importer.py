"""Testy importera danych JSONL."""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from packages.core.models import (
    JednostkaCeny,
    Oferta,
    ProfilLeczniczy,
    Udogodnienia,
    Wyzywienie,
    Zrodlo,
)
from packages.importer.procesor import importuj_adapter, importuj_wszystkie
from packages.importer.walidator import sprawdz_gotowosc_do_importu
from packages.storage.baza import BazaDanych
from packages.storage.repozytorium import FiltryOfert, RepozytoriumOfert


@pytest.fixture
def repo_pamiec() -> RepozytoriumOfert:
    baza = BazaDanych(":memory:")
    return RepozytoriumOfert(baza)


def przygotuj_katalog_adaptera(
    katalog: Path,
    adapter: str = "testowy",
    kompletny: bool = True,
    zablokowany: bool = False,
    liczba_ofert: int = 2,
) -> Path:
    kat = katalog / adapter
    kat.mkdir(parents=True, exist_ok=True)
    dzis = "2026-09-14"

    if zablokowany:
        (kat / ".run.lock").write_text("lock", encoding="utf-8")

    oferty = []
    for i in range(1, liczba_ofert + 1):
        o = Oferta(
            adapter=adapter,
            zrodlo_id=f"oferta-{i}",
            osrodek_klucz=f"{adapter}-osrodek",
            osrodek_nazwa=f"Ośrodek {adapter.title()}",
            miejscowosc="Kołobrzeg",
            nazwa_pakietu=f"Pakiet {i}",
            liczba_dni=7,
            liczba_nocy=6,
            termin_od=date(2026, 11, 1),
            termin_do=date(2026, 11, 8),
            dostepny=True,
            cena=Decimal(f"{1000 * i}.00"),
            jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
            wyzywienie=Wyzywienie.FB,
            profile=[ProfilLeczniczy.KARDIOLOGICZNY],
            udogodnienia=Udogodnienia(basen=True),
            zrodlo=Zrodlo(
                url=f"https://example.com/{i}",
                pobrano_o=datetime.now(UTC),
                adapter=adapter,
                wersja_adaptera="0.1.0",
                hash_tresci="f" * 64,
            ),
        )
        oferty.append(o)

    (kat / f"{dzis}.jsonl").write_text(
        "".join(o.model_dump_json() + "\n" for o in oferty),
        encoding="utf-8",
    )

    raport = {
        "adapter": adapter,
        "wersja_adaptera": "0.1.0",
        "wersja_kontraktu": "0.1.0",
        "start": f"{dzis}T10:00:00Z",
        "koniec": f"{dzis}T10:05:00Z",
        "url_odwiedzone": 2,
        "oferty_ok": len(oferty),
        "oferty_odrzucone": 0,
        "bledy_http": 0,
        "kompletny": kompletny,
        "bledy": [] if kompletny else [{"blad": "HTTP 500", "etap": "http"}],
        "do_kontaktu": [],
    }
    (kat / f"{dzis}.raport.json").write_text(
        json.dumps(raport, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return kat


def test_blokada_run_lock(tmp_path: Path):
    kat = przygotuj_katalog_adaptera(tmp_path, zablokowany=True)
    gotowy, komunikat, raport, plik_jsonl = sprawdz_gotowosc_do_importu(kat)
    assert not gotowy
    assert "Crawler w trakcie pracy" in komunikat
    assert plik_jsonl is None


def test_ochrona_przed_niekompletnym_przebiegiem(tmp_path: Path, repo_pamiec: RepozytoriumOfert):
    # Najpierw poprawny import
    kat = przygotuj_katalog_adaptera(tmp_path, adapter="ustron", kompletny=True, liczba_ofert=2)
    wynik = importuj_adapter(kat, repo_pamiec)
    assert wynik["status"] == "sukces"
    assert repo_pamiec.policz_aktywne_oferty() == 2

    # Następnie symulacja awarii pobierania (kompletny=false)
    przygotuj_katalog_adaptera(tmp_path, adapter="ustron", kompletny=False, liczba_ofert=0)
    wynik_awaria = importuj_adapter(kat, repo_pamiec)
    assert wynik_awaria["status"] == "pominieto"
    assert "Przebieg niekompletny" in wynik_awaria["komunikat"]

    # Poprawne dane nadal istnieją w bazie nienaruszone!
    assert repo_pamiec.policz_aktywne_oferty() == 2


def test_import_i_brak_duplikatow(tmp_path: Path, repo_pamiec: RepozytoriumOfert):
    kat = przygotuj_katalog_adaptera(tmp_path, adapter="wieniec", kompletny=True, liczba_ofert=2)
    wynik1 = importuj_adapter(kat, repo_pamiec)
    assert wynik1["status"] == "sukces"
    assert wynik1["zaimportowano"] == 2
    assert repo_pamiec.policz_aktywne_oferty() == 2

    # Ponowny import tego samego pliku
    wynik2 = importuj_adapter(kat, repo_pamiec)
    assert wynik2["status"] == "sukces"
    assert repo_pamiec.policz_aktywne_oferty() == 2


def test_import_wszystkich_adapterow(tmp_path: Path, repo_pamiec: RepozytoriumOfert):
    przygotuj_katalog_adaptera(tmp_path, adapter="a1", kompletny=True, liczba_ofert=1)
    przygotuj_katalog_adaptera(tmp_path, adapter="a2", kompletny=True, liczba_ofert=2)

    wyniki = importuj_wszystkie(tmp_path, repo_pamiec)
    assert len(wyniki) == 2
    assert repo_pamiec.policz_aktywne_oferty() == 3

    # Weryfikacja wyszukiwania w bazie
    elementy, razem = repo_pamiec.szukaj_ofert(FiltryOfert())
    assert razem == 3


@pytest.mark.parametrize("uszkodzenie", ["pusty", "uciety", "duplikat", "adapter", "kompletny"])
def test_uszkodzony_snapshot_nie_wycofuje_ofert(tmp_path, repo_pamiec, uszkodzenie):
    kat = przygotuj_katalog_adaptera(tmp_path)
    assert importuj_adapter(kat, repo_pamiec)["status"] == "sukces"
    plik = kat / "2026-09-14.jsonl"
    linie = plik.read_text(encoding="utf-8").splitlines()
    if uszkodzenie == "pusty":
        plik.write_text("", encoding="utf-8")
    elif uszkodzenie == "uciety":
        plik.write_text(linie[0] + "\n", encoding="utf-8")
    elif uszkodzenie == "duplikat":
        plik.write_text((linie[0] + "\n") * 2, encoding="utf-8")
    elif uszkodzenie == "adapter":
        rekord = json.loads(linie[0])
        rekord["adapter"] = "inny"
        rekord["zrodlo"]["adapter"] = "inny"
        plik.write_text(json.dumps(rekord) + "\n" + linie[1] + "\n", encoding="utf-8")
    else:
        raport_plik = kat / "2026-09-14.raport.json"
        raport = json.loads(raport_plik.read_text(encoding="utf-8"))
        raport["kompletny"] = "false"
        raport_plik.write_text(json.dumps(raport), encoding="utf-8")

    assert importuj_adapter(kat, repo_pamiec)["status"] != "sukces"
    assert repo_pamiec.policz_aktywne_oferty() == 2


def test_prawdziwy_kompletny_pusty_snapshot_wycofuje_oferty(tmp_path, repo_pamiec):
    kat = przygotuj_katalog_adaptera(tmp_path)
    assert importuj_adapter(kat, repo_pamiec)["status"] == "sukces"
    przygotuj_katalog_adaptera(tmp_path, liczba_ofert=0)
    assert importuj_adapter(kat, repo_pamiec)["status"] == "sukces"
    assert repo_pamiec.policz_aktywne_oferty() == 0
