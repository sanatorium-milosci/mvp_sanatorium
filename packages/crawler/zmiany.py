"""Zmiany biznesowe niezależne od czasu pobrania i zmian HTML."""

from collections.abc import Iterable

from packages.core.models import Oferta

POLA_ZMIAN = ("cena", "jednostka_ceny", "waluta", "cena_od", "termin_od", "termin_do", "dostepny")


def indeksuj(oferty: Iterable[Oferta]) -> dict[tuple[str, str], Oferta]:
    wynik: dict[tuple[str, str], Oferta] = {}
    for oferta in oferty:
        klucz = (oferta.adapter, oferta.zrodlo_id)
        if klucz in wynik:
            raise ValueError(f"Powtórzony klucz oferty: {klucz}")
        wynik[klucz] = oferta
    return wynik


def porownaj(poprzednie: Iterable[Oferta], aktualne: Iterable[Oferta]) -> dict[str, int]:
    stare, nowe = indeksuj(poprzednie), indeksuj(aktualne)
    return {
        "nowe": len(nowe.keys() - stare.keys()),
        "zmienione": sum(
            any(getattr(stare[k], pole) != getattr(nowe[k], pole) for pole in POLA_ZMIAN)
            for k in stare.keys() & nowe.keys()
        ),
        "zniknely": len(stare.keys() - nowe.keys()),
    }
