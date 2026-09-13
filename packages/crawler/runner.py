"""Orkiestracja adaptera i atomowy zapis plików wymiany ze ścieżką A."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from packages.core.models import WERSJA_KONTRAKTU, Oferta
from packages.crawler.baza import Adapter
from packages.crawler.fetch import BladPobierania, Fetch, Strona
from packages.crawler.zmiany import indeksuj, porownaj


def zapisz_atomowo(plik: Path, tekst: str) -> None:
    tymczasowy = plik.with_suffix(f".{uuid4().hex}.tmp")
    try:
        tymczasowy.write_text(tekst, encoding="utf-8")
        tymczasowy.replace(plik)
    finally:
        tymczasowy.unlink(missing_ok=True)


def _bez_pustych_stringow(wartosc: object) -> None:
    if isinstance(wartosc, str) and not wartosc.strip():
        raise ValueError("Pusty string: użyj None dla nieustalonych faktów")
    if isinstance(wartosc, dict):
        for element in wartosc.values():
            _bez_pustych_stringow(element)
    elif isinstance(wartosc, list):
        for element in wartosc:
            _bez_pustych_stringow(element)


def waliduj(rekord: Oferta, adapter: Adapter, strona: Strona) -> Oferta:
    # Ponowna walidacja słownika sprawdza też model_construct i mutacje modeli.
    dane = rekord.model_dump(mode="python")
    _bez_pustych_stringow(dane)
    oferta = Oferta.model_validate(dane)
    if oferta.adapter != adapter.nazwa or oferta.zrodlo.adapter != adapter.nazwa:
        raise ValueError("Niezgodny identyfikator adaptera w ofercie/źródle")
    if oferta.zrodlo.wersja_adaptera != adapter.wersja:
        raise ValueError("Niezgodna wersja adaptera w źródle")
    if str(oferta.zrodlo.url) != strona.url:
        raise ValueError("Źródło oferty musi wskazywać faktycznie sparsowaną stronę")
    if not re.fullmatch(r"[0-9a-f]{64}", oferta.zrodlo.hash_tresci):
        raise ValueError("hash_tresci musi być skrótem SHA-256 fragmentu źródłowego")
    for pole in ("cena", "doplata_jedynka", "oplata_klimatyczna_doba"):
        kwota = getattr(oferta, pole)
        if isinstance(dane[pole], float) or (
            kwota is not None and (not kwota.is_finite() or kwota < 0)
        ):
            raise ValueError(f"{pole}: wymagana nieujemna, skończona kwota Decimal")
    for pole in ("liczba_dni", "liczba_nocy", "liczba_zabiegow_dziennie"):
        liczba = getattr(oferta, pole)
        if liczba is not None and (liczba < 0 or (pole == "liczba_dni" and liczba == 0)):
            raise ValueError(f"{pole}: nieprawidłowa liczba")
    if oferta.termin_od and oferta.termin_do and oferta.termin_do < oferta.termin_od:
        raise ValueError("Koniec pobytu jest wcześniejszy niż początek")
    oferta.zrodlo.pobrano_o = strona.pobrano_o
    return Oferta.model_validate(oferta.model_dump(mode="python"))


async def uruchom(adapter: Adapter, fetch: Fetch, out: Path, *, pracownicy: int = 4) -> dict:
    if adapter.wymaga_js:
        raise NotImplementedError("Adaptery wymagające JS: obsługa Playwright jest etapem M3")
    if pracownicy < 1 or not re.fullmatch(r"[a-z][a-z0-9_]*", adapter.nazwa):
        raise ValueError("Nieprawidłowa liczba pracowników lub nazwa adaptera")
    if set(adapter.domeny) != fetch.domeny:
        raise ValueError("Fetch musi być ograniczony do domen bieżącego adaptera")
    katalog = out / adapter.nazwa
    katalog.mkdir(parents=True, exist_ok=True)
    blokada = katalog / ".run.lock"
    try:
        uchwyt = blokada.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError(f"Przebieg już trwa lub zostawił blokadę: {blokada}") from exc
    try:
        with uchwyt:
            uchwyt.write(datetime.now(UTC).isoformat())
        return await _przebieg(adapter, fetch, katalog, pracownicy)
    finally:
        blokada.unlink(missing_ok=True)


async def _przebieg(adapter: Adapter, fetch: Fetch, katalog: Path, pracownicy: int) -> dict:
    start = datetime.now(UTC)
    baza = katalog / ".ostatni-kompletny.jsonl"
    poprzednie = (
        [
            Oferta.model_validate_json(linia)
            for linia in baza.read_text(encoding="utf-8").splitlines()
        ]
        if baza.exists()
        else []
    )
    indeksuj(poprzednie)  # Uszkodzona baza nie może udawać pierwszego przebiegu.
    oferty: dict[tuple[str, str], Oferta] = {}
    odrzuty: list[dict] = []
    bledy: list[dict] = []
    semafor = asyncio.Semaphore(pracownicy)

    async def przetworz(url: str) -> None:
        async with semafor:
            try:
                strona = await fetch.get(url)
            except BladPobierania as exc:
                bledy.append({"url": url, "blad": str(exc), "etap": "http"})
                return
            try:
                rekordy = adapter.parsuj(strona.html, strona.url)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                # Nie utrwalamy całego HTML ani treści wyjątku parsera (mogą zawierać prozę).
                odrzuty.append({"url": url, "blad": type(exc).__name__, "etap": "parser"})
                return
            for rekord in rekordy:
                try:
                    oferta = waliduj(rekord, adapter, strona)
                    klucz = (oferta.adapter, oferta.zrodlo_id)
                    if klucz in oferty:
                        raise ValueError(f"Powtórzony zrodlo_id: {oferta.zrodlo_id}")
                    oferty[klucz] = oferta
                except (ValueError, TypeError, AttributeError) as exc:
                    blad = (
                        exc.errors(include_url=False, include_input=False, include_context=False)
                        if isinstance(exc, ValidationError)
                        else str(exc)
                    )
                    odrzuty.append({"url": url, "blad": blad, "etap": "walidacja"})

    try:
        urle = list(dict.fromkeys(await adapter.zbierz_urle(fetch)))
    except (BladPobierania, ValueError, TypeError, KeyError, AttributeError) as exc:
        bledy.append({"blad": type(exc).__name__, "etap": "odkrywanie"})
        urle = []
    await asyncio.gather(*(przetworz(url) for url in urle))
    aktualne = [oferty[k] for k in sorted(oferty)]
    kompletny = not bledy and not odrzuty
    # Puste wyniki po wcześniejszych ofertach wymagają ręcznej weryfikacji adaptera.
    # To może być zmiana HTML, lista ofert ładowana JS lub strona blokady HTTP 200.
    if poprzednie and not aktualne:
        kompletny = False
        bledy.append({"blad": "Pusty wynik po niepustym przebiegu", "etap": "kontrola"})
    stat = fetch.statystyki
    raport = {
        "adapter": adapter.nazwa,
        "wersja_adaptera": adapter.wersja,
        "wersja_kontraktu": WERSJA_KONTRAKTU,
        "start": start.isoformat(),
        "koniec": datetime.now(UTC).isoformat(),
        "url_odwiedzone": len(stat.url_odwiedzone),
        "oferty_ok": len(aktualne),
        "oferty_odrzucone": len(odrzuty),
        "bledy_http": stat.bledy_http,
        "zmiany": porownaj(poprzednie, aktualne) if kompletny else None,
        "kompletny": kompletny,
        "trafienia_cache": stat.trafienia_cache,
        "bledy": bledy,
        "do_kontaktu": [{"url": url, "powod": powod} for url, powod in stat.do_kontaktu.items()],
    }
    data = start.date().isoformat()
    jsonl = "".join(oferta.model_dump_json() + "\n" for oferta in aktualne)
    # Raport jest znacznikiem ukończenia zapisu. Konsument czeka też na brak .run.lock.
    # Po błędzie zapisu nie może zostać raport sukcesu z wcześniejszego przebiegu.
    (katalog / f"{data}.raport.json").unlink(missing_ok=True)
    zapisz_atomowo(katalog / f"{data}.jsonl", jsonl)
    zapisz_atomowo(
        katalog / f"{data}.odrzuty.jsonl",
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in odrzuty),
    )
    zapisz_atomowo(
        katalog / f"{data}.raport.json", json.dumps(raport, ensure_ascii=False, indent=2)
    )
    if kompletny:
        zapisz_atomowo(baza, jsonl)
    return raport
