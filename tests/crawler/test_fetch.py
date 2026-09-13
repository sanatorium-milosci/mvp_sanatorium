import asyncio
import json
import time

import httpx
import pytest

from packages.crawler.fetch import BladPobierania, Fetch

ORIGIN = "https://sanatorium.example"
AGENT = "SanatoriaBot/1.0 (+https://sanatorium.example/bot; kontakt@sanatorium.example)"


def html_response(text="<p>Fakty</p>"):
    return httpx.Response(200, text=text, headers={"content-type": "text/html"})


async def test_cache_dyskowy_zachowuje_czas_pobrania(fabryka_fetch):
    zapytania = []

    def handler(request):
        zapytania.append(request.url.path)
        assert request.headers["User-Agent"] == AGENT
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return html_response()

    async with fabryka_fetch(handler) as fetch:
        pierwsza = await fetch.get(ORIGIN + "/oferty")
    async with fabryka_fetch(handler) as fetch:
        druga = await fetch.get(ORIGIN + "/oferty")
        assert fetch.statystyki.trafienia_cache == 2
    assert pierwsza == druga
    assert zapytania == ["/robots.txt", "/oferty"]


@pytest.mark.parametrize("uszkodzony", [False, True])
async def test_cache_wygasly_lub_uszkodzony_jest_odswiezany(fabryka_fetch, uszkodzony):
    zapytania = []

    def handler(request):
        zapytania.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return html_response()

    async with fabryka_fetch(handler) as fetch:
        await fetch.get(ORIGIN + "/oferty")
        plik = fetch._plik_cache(ORIGIN + "/oferty")
        if uszkodzony:
            plik.write_text("{uszkodzony", encoding="utf-8")
        else:
            dane = json.loads(plik.read_text(encoding="utf-8"))
            dane["pobrano_o"] = "2020-01-01T00:00:00+00:00"
            plik.write_text(json.dumps(dane), encoding="utf-8")
        await fetch.get(ORIGIN + "/oferty")
    assert zapytania.count("/oferty") == 2


@pytest.mark.parametrize("sciezka", ["/prywatne/oferta", "/oferta.pdf"])
async def test_zakaz_robots_z_wildcardem_i_koncem_sciezki(fabryka_fetch, sciezka):
    zapytania = []

    def handler(request):
        zapytania.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nDisallow: /prywatne/*\nDisallow: /*.pdf$")

    async with fabryka_fetch(handler) as fetch:
        with pytest.raises(BladPobierania, match="robots.txt zabrania"):
            await fetch.get(ORIGIN + sciezka)
        assert ORIGIN + sciezka in fetch.statystyki.do_kontaktu
    assert zapytania == ["/robots.txt"]


@pytest.mark.parametrize("cel", ["/prywatne", "https://obca.example/oferta"])
async def test_przekierowanie_nie_omija_regul(fabryka_fetch, cel):
    zapytania = []

    def handler(request):
        zapytania.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /prywatne")
        return httpx.Response(302, headers={"Location": cel})

    async with fabryka_fetch(handler) as fetch:
        with pytest.raises(BladPobierania):
            await fetch.get(ORIGIN + "/oferta")
    assert zapytania == [ORIGIN + "/robots.txt", ORIGIN + "/oferta"]


@pytest.mark.parametrize("status", [401, 403, 500])
async def test_niedostepne_robots_nie_pozwala_na_crawlowanie(fabryka_fetch, monkeypatch, status):
    zapytania = []

    async def bez_czekania(sekundy):
        pass

    monkeypatch.setattr(asyncio, "sleep", bez_czekania)

    def handler(request):
        zapytania.append(request.url.path)
        return httpx.Response(status)

    async with fabryka_fetch(handler) as fetch:
        with pytest.raises(BladPobierania):
            await fetch.get(ORIGIN + "/oferta")
    assert set(zapytania) == {"/robots.txt"}
    assert len(zapytania) == (3 if status == 500 else 1)


async def test_404_robots_jest_dozwolonym_brakiem_pliku(fabryka_fetch):
    def handler(request):
        return httpx.Response(404) if request.url.path == "/robots.txt" else html_response()

    async with fabryka_fetch(handler) as fetch:
        assert (await fetch.get(ORIGIN + "/oferta")).html == "<p>Fakty</p>"


@pytest.mark.parametrize("status", [429, 503])
async def test_trzy_proby_i_wykladniczy_backoff(fabryka_fetch, monkeypatch, status):
    opoznienia, zapytania = [], []

    async def zapisz_czekanie(sekundy):
        opoznienia.append(sekundy)

    monkeypatch.setattr(asyncio, "sleep", zapisz_czekanie)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        zapytania.append(request.url.path)
        return httpx.Response(status)

    async with fabryka_fetch(handler) as fetch:
        with pytest.raises(BladPobierania):
            await fetch.get(ORIGIN + "/oferty")
        assert fetch.statystyki.bledy_http == 3
    assert len(zapytania) == 3
    assert opoznienia == [1, 2]


async def test_retry_after_jest_respektowane(fabryka_fetch, monkeypatch):
    opoznienia, proby = [], []

    async def zapisz_czekanie(sekundy):
        opoznienia.append(sekundy)

    monkeypatch.setattr(asyncio, "sleep", zapisz_czekanie)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        proby.append(1)
        if len(proby) == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return html_response()

    async with fabryka_fetch(handler) as fetch:
        await fetch.get(ORIGIN + "/oferty")
    assert opoznienia == [7]


async def test_limit_dotyczy_domeny_a_inna_moze_pracowac_rownolegle(tmp_path, monkeypatch):
    zegar = [100.0]
    opoznienia = []

    async def przesun(sekundy):
        opoznienia.append(sekundy)
        zegar[0] += sekundy

    monkeypatch.setattr(time, "monotonic", lambda: zegar[0])
    monkeypatch.setattr(asyncio, "sleep", przesun)
    async with Fetch(
        user_agent=AGENT, domeny=["sanatorium.example", "inne.example"], cache_dir=tmp_path
    ) as fetch:
        await fetch._odczekaj(ORIGIN + "/a")
        await fetch._odczekaj("https://inne.example/a")
        assert opoznienia == []
        await fetch._odczekaj(ORIGIN + "/b")
        await fetch._odczekaj(ORIGIN + "/c")
    assert opoznienia == [1, 1]


async def test_crawl_delay_i_request_rate_moga_zwolnic_bota(fabryka_fetch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(
                200, text="User-agent: *\nAllow: /\nCrawl-delay: 2\nRequest-rate: 1/5"
            )
        return html_response()

    async with fabryka_fetch(handler) as fetch:
        await fetch.get(ORIGIN + "/oferty")
        assert fetch._opoznienia["sanatorium.example"] == 5
