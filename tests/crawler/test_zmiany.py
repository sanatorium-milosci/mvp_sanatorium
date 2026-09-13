from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from packages.crawler.zmiany import porownaj


def test_nowa_zmieniona_zniknieta(oferta):
    stara = oferta.model_copy(update={"zrodlo_id": "usunieta"})
    nowa = oferta.model_copy(update={"zrodlo_id": "nowa"})
    zmieniona = oferta.model_copy(update={"cena": Decimal("1500.00")})
    assert porownaj([oferta, stara], [zmieniona, nowa]) == {
        "nowe": 1,
        "zmienione": 1,
        "zniknely": 1,
    }


@pytest.mark.parametrize(
    ("pole", "wartosc"),
    [
        ("termin_od", date(2026, 10, 1)),
        ("termin_do", date(2026, 10, 7)),
        ("dostepny", False),
        ("cena", None),
        ("cena_od", True),
        ("waluta", "EUR"),
    ],
)
def test_zmiana_faktu_handlowego(oferta, pole, wartosc):
    assert porownaj([oferta], [oferta.model_copy(update={pole: wartosc})])["zmienione"] == 1


def test_czas_i_html_nie_tworza_falszywych_alertow(oferta):
    nowa = oferta.model_copy(deep=True)
    nowa.zrodlo.pobrano_o = datetime(2026, 9, 10, tzinfo=UTC)
    nowa.zrodlo.hash_tresci = "0" * 64
    assert porownaj([oferta], [nowa]) == {"nowe": 0, "zmienione": 0, "zniknely": 0}


def test_duplikaty_to_blad(oferta):
    with pytest.raises(ValueError, match="Powtórzony klucz"):
        porownaj([], [oferta, oferta])
