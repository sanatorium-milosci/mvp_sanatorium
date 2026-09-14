"""Wstrzykiwanie zależności dla tras API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from packages.storage.baza import DOMYSLNA_SCIEZKA_BAZY, BazaDanych
from packages.storage.repozytorium import RepozytoriumOfert

_domyslne_repozytorium: RepozytoriumOfert | None = None


def pobierz_repozytorium(request: Request) -> RepozytoriumOfert:
    """Zwraca instancję repozytorium przypisaną do stanu aplikacji lub globalną."""
    if hasattr(request.app.state, "repozytorium") and request.app.state.repozytorium:
        return request.app.state.repozytorium

    global _domyslne_repozytorium
    if _domyslne_repozytorium is None:
        baza = BazaDanych(DOMYSLNA_SCIEZKA_BAZY)
        _domyslne_repozytorium = RepozytoriumOfert(baza)
    return _domyslne_repozytorium


RepoDep = Annotated[RepozytoriumOfert, Depends(pobierz_repozytorium)]
