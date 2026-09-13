from datetime import UTC, datetime
from importlib.resources import files

import httpx
import pytest

from packages.crawler.adaptery.demo import URL_DEMO, AdapterDemo
from packages.crawler.fetch import Fetch, Strona

AGENT = "SanatoriaBot/1.0 (+https://sanatorium.example/bot; kontakt@sanatorium.example)"


@pytest.fixture(autouse=True)
def bez_prawdziwej_sieci(monkeypatch):
    async def zablokuj_async(*args, **kwargs):
        raise AssertionError("Testy nie mogą korzystać z prawdziwej sieci")

    def zablokuj_sync(*args, **kwargs):
        raise AssertionError("Testy nie mogą korzystać z prawdziwej sieci")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", zablokuj_async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", zablokuj_sync)


@pytest.fixture
def html_demo():
    return files("packages.crawler").joinpath("dane_demo/oferty.html").read_text(encoding="utf-8")


@pytest.fixture
def oferta(html_demo):
    return AdapterDemo().parsuj(html_demo, URL_DEMO)[0]


@pytest.fixture
def strona(html_demo):
    return Strona(URL_DEMO, html_demo, datetime(2026, 9, 10, 12, tzinfo=UTC))


@pytest.fixture
def fabryka_fetch(tmp_path, monkeypatch):
    async def bez_czekania(self, url):
        pass

    monkeypatch.setattr(Fetch, "_odczekaj", bez_czekania)

    def zbuduj(handler, **kwargs):
        return Fetch(
            user_agent=AGENT,
            domeny=["sanatorium.example"],
            cache_dir=tmp_path / "cache",
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    return zbuduj
