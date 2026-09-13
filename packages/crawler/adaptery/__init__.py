"""Dodawaj tu zweryfikowane adaptery, po jednym na domenę."""

from packages.crawler.baza import RejestrAdapterow


def rejestr_produkcyjny() -> RejestrAdapterow:
    # Lista ośrodków M1 nie została jeszcze przekazana.
    return RejestrAdapterow()
