"""Czyste parsery, jawny rejestr i wspólne narzędzia adapterów."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from packages.core.models import Oferta, Zrodlo
from packages.crawler.fetch import Fetch

# Parser nie zna zegara. Runner zastępuje tę wartość czasem pobrania strony,
# również przy odczycie z cache (wtedy zachowuje oryginalną datę pobrania).
CZAS_PARSERA = datetime(1970, 1, 1, tzinfo=UTC)


class Adapter(Protocol):
    nazwa: str
    wersja: str
    domeny: list[str]
    wymaga_js: bool

    async def zbierz_urle(self, fetch: Fetch) -> list[str]:
        """Odkrywanie ofert i paginacja; cała sieć wyłącznie przez Fetch."""
        ...

    def parsuj(self, html: str, url: str) -> list[Oferta]:
        """Czysta, deterministyczna funkcja: HTML -> fakty, bez sieci i zegara."""
        ...


class RejestrAdapterow:
    def __init__(self) -> None:
        self._adaptery: dict[str, Adapter] = {}

    def dodaj(self, adapter: Adapter) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", adapter.nazwa):
            raise ValueError("Nazwa adaptera musi być bezpiecznym identyfikatorem")
        if adapter.nazwa in self._adaptery:
            raise ValueError(f"Adapter już zarejestrowany: {adapter.nazwa}")
        self._adaptery[adapter.nazwa] = adapter

    def pobierz(self, nazwa: str) -> Adapter:
        try:
            return self._adaptery[nazwa]
        except KeyError as exc:
            raise ValueError(f"Nieznany adapter: {nazwa}") from exc

    def nazwy(self) -> list[str]:
        return sorted(self._adaptery)


def parsuj_cene(tekst: str | None) -> Decimal | None:
    """Ścisły parser kwot PLN; zakresy, proza i niejednoznaczne ceny są błędem."""
    if tekst is None or not tekst.strip():
        return None
    tekst = tekst.replace("\u00a0", " ").replace("\u202f", " ").strip()
    dopasowanie = re.fullmatch(
        r"(?:od\s+)?(\d{1,3}(?: \d{3})+|\d+)([,.]\d{2})?\s*(?:zł|PLN)?",
        tekst,
        flags=re.IGNORECASE,
    )
    if not dopasowanie:
        raise ValueError(f"Niejednoznaczny format ceny: {tekst!r}")
    calosc, grosze = dopasowanie.groups()
    return Decimal(calosc.replace(" ", "") + (grosze or "").replace(",", "."))


def zrodlo_fragmentu(fragment: str, url: str, adapter: str, wersja: str) -> Zrodlo:
    return Zrodlo(
        url=url,
        pobrano_o=CZAS_PARSERA,
        adapter=adapter,
        wersja_adaptera=wersja,
        hash_tresci=hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
    )
