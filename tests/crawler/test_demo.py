from decimal import Decimal
from pathlib import Path

import pytest

from packages.core.models import JednostkaCeny, Oferta
from packages.crawler.adaptery.demo import URL_DEMO, AdapterDemo
from packages.crawler.baza import CZAS_PARSERA, RejestrAdapterow, parsuj_cene


def test_konkretne_fakty_i_deterministyczny_parser(html_demo):
    adapter = AdapterDemo()
    oferty = adapter.parsuj(html_demo, URL_DEMO)
    assert len(oferty) == 2
    oferta = oferty[0]
    assert oferta.cena == Decimal("1290.00")
    assert oferta.jednostka_ceny == JednostkaCeny.TURNUS_OSOBA
    assert (oferta.liczba_dni, oferta.liczba_nocy, oferta.dostepny) == (7, 6, True)
    assert oferta.termin_od is None
    assert oferta.profile == []
    assert oferta.zrodlo.pobrano_o == CZAS_PARSERA
    assert oferty == adapter.parsuj(html_demo, URL_DEMO)
    zmieniona = adapter.parsuj(html_demo.replace("1 290,00", "1 490,00"), URL_DEMO)[0]
    assert zmieniona.zrodlo_id == oferta.zrodlo_id
    assert zmieniona.zrodlo.hash_tresci != oferta.zrodlo.hash_tresci


def test_brak_ceny_i_wyprzedana_oferta():
    html = (Path(__file__).parents[1] / "fixtures/crawler/demo/brak_ceny.html").read_text(
        encoding="utf-8"
    )
    oferta = AdapterDemo().parsuj(html, URL_DEMO)[0]
    assert oferta.cena is None
    assert oferta.dostepny is False
    assert oferta.termin_od is None and oferta.termin_do is None
    assert Oferta.model_validate_json(oferta.model_dump_json()) == oferta


def test_nieoczekiwany_html_nie_udaje_pustej_listy():
    with pytest.raises(ValueError, match="Brak oczekiwanej tabeli"):
        AdapterDemo().parsuj("<html>Strona chwilowo niedostępna</html>", URL_DEMO)


@pytest.mark.parametrize(
    ("tekst", "wynik"),
    [
        ("1 290,00 zł", "1290.00"),
        ("od 99,99 PLN", "99.99"),
        ("1\u00a0290,10", "1290.10"),
        ("1\u202f290,10", "1290.10"),
        ("990", "990"),
        ("1290.00", "1290.00"),
    ],
)
def test_decimal_bez_float(tekst, wynik):
    cena = parsuj_cene(tekst)
    assert isinstance(cena, Decimal)
    assert cena == Decimal(wynik)


@pytest.mark.parametrize("tekst", [None, "", " "])
def test_nieznana_cena(tekst):
    assert parsuj_cene(tekst) is None


@pytest.mark.parametrize("tekst", ["1290-1490 zł", "1,2 zł", "-10 zł", "1 29 zł", "Zapytaj"])
def test_nie_zgadujemy_cen(tekst):
    with pytest.raises(ValueError):
        parsuj_cene(tekst)


def test_rejestr_nie_nadpisuje_adaptera():
    rejestr = RejestrAdapterow()
    rejestr.dodaj(AdapterDemo())
    assert rejestr.nazwy() == ["demo"]
    with pytest.raises(ValueError, match="już zarejestrowany"):
        rejestr.dodaj(AdapterDemo())
