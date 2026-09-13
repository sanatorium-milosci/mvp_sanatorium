import json
from datetime import date
from decimal import Decimal

import httpx
import pytest

from packages.core.models import Oferta
from packages.crawler import runner
from packages.crawler.adaptery.demo import AdapterDemo
from packages.crawler.runner import uruchom, waliduj


def handler_html(html, status=200):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(status, text=html, headers={"content-type": "text/html"})

    return handler


async def test_jsonl_decimal_i_drugi_przebieg_tego_samego_dnia(tmp_path, fabryka_fetch, html_demo):
    out = tmp_path / "out"
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        pierwszy = await uruchom(AdapterDemo(), fetch, out)
    plik = next(p for p in (out / "demo").glob("[0-9]*.jsonl") if ".odrzuty." not in p.name)
    rekordy = [json.loads(linia) for linia in plik.read_text(encoding="utf-8").splitlines()]
    assert pierwszy["kompletny"] is True
    assert pierwszy["zmiany"] == {"nowe": 2, "zmienione": 0, "zniknely": 0}
    wyceniona = next(rekord for rekord in rekordy if rekord["zrodlo_id"] == "pobyt-7")
    assert wyceniona["cena"] == "1290.00"
    assert wyceniona["zrodlo"]["pobrano_o"] != "1970-01-01T00:00:00Z"
    assert all(Oferta.model_validate(rekord) for rekord in rekordy)
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        drugi = await uruchom(AdapterDemo(), fetch, out)
    assert drugi["zmiany"] == {"nowe": 0, "zmienione": 0, "zniknely": 0}
    assert drugi["trafienia_cache"] == 2
    assert not (out / "demo/.run.lock").exists()


@pytest.mark.parametrize("tryb", ["http", "parser", "pusty"])
async def test_awaria_nie_zglasza_znikniec_i_zachowuje_baze(
    tmp_path, fabryka_fetch, html_demo, tryb
):
    out = tmp_path / "out"
    async with fabryka_fetch(handler_html(html_demo), ttl=0) as fetch:
        await uruchom(AdapterDemo(), fetch, out)
    baza = out / "demo/.ostatni-kompletny.jsonl"
    poprzednia_baza = baza.read_bytes()
    html = "<table id='oferty'><tbody></tbody></table>" if tryb == "pusty" else "Brak treści"
    status = 403 if tryb == "http" else 200
    async with fabryka_fetch(handler_html(html, status), ttl=0) as fetch:
        raport = await uruchom(AdapterDemo(), fetch, out)
    assert raport["kompletny"] is False
    assert raport["zmiany"] is None
    assert baza.read_bytes() == poprzednia_baza
    if tryb == "http":
        assert raport["do_kontaktu"][0]["powod"] == "HTTP 403"
    # Po odzyskaniu strony porównujemy z ostatnim sukcesem, a nie z pustym błędem.
    async with fabryka_fetch(
        handler_html(html_demo.replace("1 290,00", "1 490,00")), ttl=0
    ) as fetch:
        naprawiony = await uruchom(AdapterDemo(), fetch, out)
    assert naprawiony["zmiany"] == {"nowe": 0, "zmienione": 1, "zniknely": 0}


async def test_rzeczywiste_usuniecie_jednej_oferty(tmp_path, fabryka_fetch, html_demo):
    out = tmp_path / "out"
    async with fabryka_fetch(handler_html(html_demo), ttl=0) as fetch:
        await uruchom(AdapterDemo(), fetch, out)
    html = "\n".join(linia for linia in html_demo.splitlines() if 'data-id="pobyt-14"' not in linia)
    async with fabryka_fetch(handler_html(html), ttl=0) as fetch:
        raport = await uruchom(AdapterDemo(), fetch, out)
    assert raport["zmiany"] == {"nowe": 0, "zmienione": 0, "zniknely": 1}


@pytest.mark.parametrize(
    ("pole", "wartosc"),
    [("cena", Decimal("-1")), ("liczba_dni", 0), ("miejscowosc", ""), ("adapter", "inny")],
)
def test_dodatkowa_walidacja_nie_zmienia_kontraktu(oferta, strona, pole, wartosc):
    oferta = oferta.model_copy(update={pole: wartosc})
    with pytest.raises(ValueError):
        waliduj(oferta, AdapterDemo(), strona)


def test_odwrocone_daty_sa_odrzucane(oferta, strona):
    oferta.termin_od = date(2026, 10, 2)
    oferta.termin_do = date(2026, 10, 1)
    with pytest.raises(ValueError, match="Koniec pobytu"):
        waliduj(oferta, AdapterDemo(), strona)


async def test_odrzut_walidacji_i_duplikat_nie_trafiaja_do_wyjscia(
    tmp_path, fabryka_fetch, html_demo
):
    class WadliwyAdapter(AdapterDemo):
        def parsuj(self, html, url):
            oferty = super().parsuj(html, url)
            return [oferty[0], oferty[0], oferty[1].model_copy(update={"cena": Decimal("-1")})]

    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        raport = await uruchom(WadliwyAdapter(), fetch, tmp_path / "out")
    assert raport["oferty_ok"] == 1
    assert raport["oferty_odrzucone"] == 2
    assert raport["kompletny"] is False
    plik = next((tmp_path / "out/demo").glob("*.odrzuty.jsonl"))
    assert all(
        "blad" in json.loads(linia) for linia in plik.read_text(encoding="utf-8").splitlines()
    )


async def test_nie_pozwalamy_na_rownoczesny_zapis(tmp_path, fabryka_fetch, html_demo):
    katalog = tmp_path / "out/demo"
    katalog.mkdir(parents=True)
    blokada = katalog / ".run.lock"
    blokada.write_text("inny proces", encoding="utf-8")
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        with pytest.raises(RuntimeError, match="Przebieg już trwa"):
            await uruchom(AdapterDemo(), fetch, tmp_path / "out")
    assert blokada.read_text(encoding="utf-8") == "inny proces"


async def test_blad_zapisu_nie_zostawia_starego_raportu_sukcesu(
    tmp_path, fabryka_fetch, html_demo, monkeypatch
):
    out = tmp_path / "out"
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        await uruchom(AdapterDemo(), fetch, out)

    def blad_dysku(plik, tekst):
        raise OSError("Brak miejsca")

    monkeypatch.setattr(runner, "zapisz_atomowo", blad_dysku)
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        with pytest.raises(OSError, match="Brak miejsca"):
            await uruchom(AdapterDemo(), fetch, out)
    assert not list((out / "demo").glob("*.raport.json"))
    assert (out / "demo/.ostatni-kompletny.jsonl").exists()


async def test_js_ma_jawny_blad_zamiast_pozornego_sukcesu(tmp_path, fabryka_fetch, html_demo):
    adapter = AdapterDemo()
    adapter.wymaga_js = True
    async with fabryka_fetch(handler_html(html_demo)) as fetch:
        with pytest.raises(NotImplementedError, match="Playwright"):
            await uruchom(adapter, fetch, tmp_path)
