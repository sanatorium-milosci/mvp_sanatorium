"""Testy warstwy bazy danych i repozytorium ofert."""

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
from packages.storage.baza import BazaDanych
from packages.storage.repozytorium import FiltryOfert, RepozytoriumOfert


@pytest.fixture
def repo_pamiec() -> RepozytoriumOfert:
    baza = BazaDanych(":memory:")
    return RepozytoriumOfert(baza)


def stworz_oferte(
    zrodlo_id: str,
    adapter: str = "demo",
    cena: Decimal | None = Decimal("1200.00"),
    miejscowosc: str = "Ciechocinek",
    dni: int = 14,
    basen: bool | None = True,
) -> Oferta:
    return Oferta(
        adapter=adapter,
        zrodlo_id=zrodlo_id,
        osrodek_klucz=f"{adapter}-osrodek",
        osrodek_nazwa=f"Ośrodek {adapter}",
        miejscowosc=miejscowosc,
        nazwa_pakietu=f"Pakiet {zrodlo_id}",
        liczba_dni=dni,
        liczba_nocy=dni - 1,
        termin_od=date(2026, 10, 1),
        termin_do=date(2026, 10, 15),
        dostepny=True,
        cena=cena,
        jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
        wyzywienie=Wyzywienie.FB,
        profile=[ProfilLeczniczy.KARDIOLOGICZNY],
        udogodnienia=Udogodnienia(basen=basen, winda=True),
        zrodlo=Zrodlo(
            url="https://example.com/oferta",
            pobrano_o=datetime.now(UTC),
            adapter=adapter,
            wersja_adaptera="0.1.0",
            hash_tresci="a" * 64,
        ),
    )


def test_inicjalizacja_i_upsert(repo_pamiec: RepozytoriumOfert):
    oferta1 = stworz_oferte("o-1", cena=Decimal("1500.00"))
    oferta2 = stworz_oferte("o-2", cena=Decimal("2000.00"))

    # Pierwszy zapis
    wynik1 = repo_pamiec.upsert_oferty("demo", [oferta1, oferta2])
    assert wynik1["dodane"] == 2
    assert wynik1["zaktualizowane"] == 0
    assert wynik1["dezaktywowane"] == 0
    assert repo_pamiec.policz_aktywne_oferty() == 2

    # Powtórny zapis bez zmian
    wynik2 = repo_pamiec.upsert_oferty("demo", [oferta1, oferta2])
    assert wynik2["dodane"] == 0
    assert wynik2["zaktualizowane"] == 2
    assert repo_pamiec.policz_aktywne_oferty() == 2

    # Zapis z wycofaną jedną ofertą
    wynik3 = repo_pamiec.upsert_oferty("demo", [oferta1], oznacz_brakujace_nieaktywne=True)
    assert wynik3["dezaktywowane"] == 1
    assert repo_pamiec.policz_aktywne_oferty() == 1


def test_wyszukiwanie_i_filtry(repo_pamiec: RepozytoriumOfert):
    o1 = stworz_oferte("o-1", miejscowosc="Ustroń", cena=Decimal("1000.00"), dni=7, basen=True)
    o2 = stworz_oferte(
        "o-2", miejscowosc="Ciechocinek", cena=Decimal("3000.00"), dni=14, basen=False
    )
    repo_pamiec.upsert_oferty("demo", [o1, o2])

    # Filtr miejscowości
    elementy, razem = repo_pamiec.szukaj_ofert(FiltryOfert(miejscowosc="Ustroń"))
    assert razem == 1
    assert elementy[0]["zrodlo_id"] == "o-1"

    # Filtr ceny
    elementy, razem = repo_pamiec.szukaj_ofert(FiltryOfert(cena_max=Decimal("1500.00")))
    assert razem == 1
    assert elementy[0]["zrodlo_id"] == "o-1"

    # Filtr udogodnienia basen
    elementy, razem = repo_pamiec.szukaj_ofert(FiltryOfert(basen=True))
    assert razem == 1
    assert elementy[0]["udogodnienia"]["basen"] is True

    # Wyszukiwanie tekstowe q
    elementy, razem = repo_pamiec.szukaj_ofert(FiltryOfert(q="Ciechocinek"))
    assert razem == 1
    assert elementy[0]["miejscowosc"] == "Ciechocinek"


def test_stronicowanie(repo_pamiec: RepozytoriumOfert):
    oferty = [stworz_oferte(f"id-{i}", cena=Decimal(f"{1000 + i * 100}.00")) for i in range(15)]
    repo_pamiec.upsert_oferty("demo", oferty)

    # Strona 1, po 5 na stronę
    elem_str1, razem = repo_pamiec.szukaj_ofert(
        FiltryOfert(strona=1, na_stronie=5, sortuj="cena_asc")
    )
    assert razem == 15
    assert len(elem_str1) == 5
    assert elem_str1[0]["cena"] == "1000.00"

    # Strona 2
    elem_str2, razem = repo_pamiec.szukaj_ofert(
        FiltryOfert(strona=2, na_stronie=5, sortuj="cena_asc")
    )
    assert len(elem_str2) == 5
    assert elem_str2[0]["cena"] == "1500.00"


def test_metadane_filtrow(repo_pamiec: RepozytoriumOfert):
    o1 = stworz_oferte("o-1", miejscowosc="Ustroń", cena=Decimal("1000.00"), dni=7)
    o2 = stworz_oferte("o-2", miejscowosc="Ciechocinek", cena=Decimal("2500.00"), dni=14)
    repo_pamiec.upsert_oferty("demo", [o1, o2])

    meta = repo_pamiec.pobierz_filtry_metadane()
    assert "Ustroń" in meta["miejscowosci"]
    assert "Ciechocinek" in meta["miejscowosci"]
    assert meta["min_dni"] == 7
    assert meta["max_dni"] == 14
    assert meta["liczba_ofert_razem"] == 2


def test_kopia_zapasowa(tmp_path: Path):
    sciezka_bazy = tmp_path / "baza.db"
    baza = BazaDanych(sciezka_bazy)
    repo = RepozytoriumOfert(baza)
    repo.upsert_oferty("demo", [stworz_oferte("o-1")])

    sciezka_kopii = tmp_path / "kopia.db"
    baza.wykonaj_kopie_zapasowa(sciezka_kopii)
    assert sciezka_kopii.exists()

    baza_kopii = BazaDanych(sciezka_kopii)
    repo_kopii = RepozytoriumOfert(baza_kopii)
    assert repo_kopii.policz_aktywne_oferty() == 1
