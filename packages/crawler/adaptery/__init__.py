"""Dodawaj tu zweryfikowane adaptery, po jednym na domenę."""

from packages.crawler.adaptery.bristol import AdapterBristol
from packages.crawler.adaptery.promien import AdapterPromien
from packages.crawler.adaptery.znp import AdapterZnp
from packages.crawler.baza import RejestrAdapterow


def rejestr_produkcyjny() -> RejestrAdapterow:
    rejestr = RejestrAdapterow()
    for adapter in (AdapterBristol(), AdapterPromien(), AdapterZnp()):
        rejestr.dodaj(adapter)
    return rejestr
