"""Uprzejma sieć: robots.txt, ograniczone domeny, cache, retry i limity."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import httpx
from protego import Protego


class BladPobierania(RuntimeError):
    """Pobranie niedozwolone lub zakończone niepowodzeniem."""


@dataclass(frozen=True)
class Strona:
    url: str
    html: str
    pobrano_o: datetime


@dataclass
class Statystyki:
    url_odwiedzone: set[str] = field(default_factory=set)
    bledy_http: int = 0
    trafienia_cache: int = 0
    do_kontaktu: dict[str, str] = field(default_factory=dict)


class Fetch:
    def __init__(
        self,
        *,
        user_agent: str,
        domeny: list[str],
        cache_dir: Path,
        wspolbieznosc: int = 4,
        odstep: float = 1.0,
        ttl: float = 86400,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not user_agent.startswith("SanatoriaBot/") or "https://" not in user_agent:
            raise ValueError("User-Agent musi zawierać SanatoriaBot i stronę informacyjną HTTPS")
        if "@" not in user_agent or "<" in user_agent or "twoja-domena" in user_agent:
            raise ValueError("Ustaw rzeczywisty kontakt w User-Agent")
        if wspolbieznosc < 1 or odstep < 1 or ttl < 0:
            raise ValueError("Współbieżność >= 1, odstęp >= 1 s, TTL >= 0")
        self.user_agent = user_agent
        self.domeny = {d.lower() for d in domeny}
        self.cache_dir = cache_dir
        self.odstep = odstep
        self.ttl = ttl
        self.statystyki = Statystyki()
        self._semafor = asyncio.Semaphore(wspolbieznosc)
        self._blokady: dict[str, asyncio.Lock] = {}
        self._ostatnio: dict[str, float] = {}
        self._robots: dict[str, Protego] = {}
        self._robots_blokady: dict[str, asyncio.Lock] = {}
        self._opoznienia: dict[str, float] = {}
        self._klient = httpx.AsyncClient(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(30),
            follow_redirects=False,
            transport=transport,
            limits=httpx.Limits(max_connections=wspolbieznosc),
        )

    async def __aenter__(self) -> Fetch:
        await self._klient.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._klient.aclose()

    def _sprawdz_url(self, url: str) -> str:
        czesci = urlsplit(url)
        if (
            czesci.scheme not in {"http", "https"}
            or czesci.hostname not in self.domeny
            or czesci.username is not None
            or czesci.password is not None
            or czesci.port not in {None, 80, 443}
        ):
            raise BladPobierania(f"URL poza publicznymi domenami adaptera: {url}")
        return f"{czesci.scheme}://{czesci.netloc}"

    def _plik_cache(self, url: str) -> Path:
        # Osobny cache polityki i stron dla każdej tożsamości bota.
        klucz = hashlib.sha256(f"{self.user_agent}\n{url}".encode()).hexdigest()
        return self.cache_dir / f"{klucz}.json"

    def _z_cache(self, url: str) -> Strona | None:
        try:
            dane = json.loads(self._plik_cache(url).read_text(encoding="utf-8"))
            czas = datetime.fromisoformat(dane["pobrano_o"])
            wiek = (datetime.now(UTC) - czas).total_seconds()
            if dane["url"] == url and 0 <= wiek < self.ttl and isinstance(dane["html"], str):
                self.statystyki.trafienia_cache += 1
                return Strona(url, dane["html"], czas)
        except (OSError, ValueError, KeyError, TypeError):
            pass  # Uszkodzony cache wymaga ponownego, zwykłego pobrania.
        return None

    def _do_cache(self, strona: Strona) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        plik = self._plik_cache(strona.url)
        tymczasowy = plik.with_suffix(f".{uuid4().hex}.tmp")
        try:
            tymczasowy.write_text(
                json.dumps(
                    {
                        "url": strona.url,
                        "html": strona.html,
                        "pobrano_o": strona.pobrano_o.isoformat(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            tymczasowy.replace(plik)
        finally:
            tymczasowy.unlink(missing_ok=True)

    async def _odczekaj(self, url: str) -> None:
        domena = urlsplit(url).hostname or ""
        async with self._blokady.setdefault(domena, asyncio.Lock()):
            odstep = max(self.odstep, self._opoznienia.get(domena, 0))
            czekaj = self._ostatnio.get(domena, -float("inf")) + odstep - time.monotonic()
            if czekaj > 0:
                await asyncio.sleep(czekaj)
            self._ostatnio[domena] = time.monotonic()

    @staticmethod
    def _retry_after(odpowiedz: httpx.Response) -> float:
        wartosc = odpowiedz.headers.get("Retry-After", "0")
        try:
            return max(0, float(wartosc))
        except ValueError:
            try:
                return max(0, (parsedate_to_datetime(wartosc) - datetime.now(UTC)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                return 0

    async def _zadaj(self, url: str) -> httpx.Response:
        self._sprawdz_url(url)
        for proba in range(3):
            try:
                async with self._semafor:
                    await self._odczekaj(url)
                    self.statystyki.url_odwiedzone.add(url)
                    odpowiedz = await self._klient.get(url)
            except httpx.TransportError as exc:
                self.statystyki.bledy_http += 1
                if proba == 2:
                    raise BladPobierania(f"Błąd połączenia: {url}") from exc
                await asyncio.sleep(2**proba)
                continue
            if odpowiedz.status_code >= 400:
                self.statystyki.bledy_http += 1
            if odpowiedz.status_code in {401, 403}:
                self.statystyki.do_kontaktu[url] = f"HTTP {odpowiedz.status_code}"
            if odpowiedz.status_code != 429 and odpowiedz.status_code < 500:
                return odpowiedz
            if odpowiedz.status_code == 429:
                self.statystyki.do_kontaktu[url] = "HTTP 429 — ograniczenie dostępu"
            opoznienie = max(2**proba, self._retry_after(odpowiedz))
            if proba == 2 or opoznienie > 120:
                raise BladPobierania(f"HTTP {odpowiedz.status_code}; odroczono pobranie: {url}")
            await asyncio.sleep(opoznienie)
        raise AssertionError("Nieosiągalna gałąź retry")

    async def _robots_dla(self, url: str) -> Protego:
        origin = self._sprawdz_url(url)
        async with self._robots_blokady.setdefault(origin, asyncio.Lock()):
            if origin in self._robots:
                return self._robots[origin]
            robots_url = f"{origin}/robots.txt"
            strona = self._z_cache(robots_url)
            if strona is None:
                cel = robots_url
                for _ in range(6):
                    odpowiedz = await self._zadaj(cel)
                    if odpowiedz.is_redirect:
                        cel = urljoin(cel, odpowiedz.headers.get("location", ""))
                        if self._sprawdz_url(cel) != origin:
                            raise BladPobierania("Przekierowanie robots.txt poza origin")
                        continue
                    break
                else:
                    raise BladPobierania("Zbyt wiele przekierowań robots.txt")
                if odpowiedz.status_code in {404, 410}:
                    tekst = "User-agent: *\nAllow: /"
                elif odpowiedz.status_code == 200:
                    tekst = odpowiedz.text
                    if "<html" in tekst.lower() or "<!doctype html" in tekst.lower():
                        raise BladPobierania("Otrzymano HTML zamiast robots.txt")
                else:
                    raise BladPobierania(
                        f"Nie można ustalić robots.txt: HTTP {odpowiedz.status_code}"
                    )
                strona = Strona(robots_url, tekst, datetime.now(UTC))
                self._do_cache(strona)
            parser = Protego.parse(strona.html)
            domena = urlsplit(url).hostname or ""
            agent = self.user_agent.split("/", 1)[0]
            opoznienie = parser.crawl_delay(agent) or 0
            tempo = parser.request_rate(agent)
            if tempo and tempo.requests > 0:
                opoznienie = max(opoznienie, tempo.seconds / tempo.requests)
            self._opoznienia[domena] = max(self._opoznienia.get(domena, 0), opoznienie)
            self._robots[origin] = parser
            return parser

    async def get(self, url: str) -> Strona:
        for _ in range(6):
            self._sprawdz_url(url)
            parser = await self._robots_dla(url)
            if not parser.can_fetch(url, self.user_agent.split("/", 1)[0]):
                self.statystyki.do_kontaktu[url] = "Zakaz robots.txt"
                raise BladPobierania(f"robots.txt zabrania pobrania: {url}")
            if strona := self._z_cache(url):
                return strona
            odpowiedz = await self._zadaj(url)
            if odpowiedz.is_redirect:
                if not odpowiedz.headers.get("location"):
                    raise BladPobierania("Przekierowanie bez Location")
                url = urljoin(url, odpowiedz.headers["location"])
                continue  # Nowy URL musi ponownie przejść reguły domen i robots.txt.
            if odpowiedz.status_code != 200:
                raise BladPobierania(f"HTTP {odpowiedz.status_code}: {url}")
            typ = odpowiedz.headers.get("content-type", "").split(";", 1)[0].lower()
            if typ not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise BladPobierania(f"Nieobsługiwany typ treści {typ!r}: {url}")
            strona = Strona(str(odpowiedz.url), odpowiedz.text, datetime.now(UTC))
            self._do_cache(strona)
            return strona
        raise BladPobierania("Zbyt wiele przekierowań strony")
