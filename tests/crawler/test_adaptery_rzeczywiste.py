import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup

from packages.core.models import JednostkaCeny, Oferta, TypPokoju
from packages.crawler.adaptery import rejestr_produkcyjny
from packages.crawler.adaptery.bristol import URL as BRISTOL_URL
from packages.crawler.adaptery.bristol import AdapterBristol
from packages.crawler.adaptery.promien import URL as PROMIEN_URL
from packages.crawler.adaptery.promien import AdapterPromien
from packages.crawler.adaptery.znp import URL as ZNP_URL
from packages.crawler.adaptery.znp import AdapterZnp
from packages.crawler.fetch import Fetch
from packages.crawler.runner import uruchom

PRZYPADKI = [
    ("promien", AdapterPromien, PROMIEN_URL, 180),
    ("bristol", AdapterBristol, BRISTOL_URL, 12),
    ("znp", AdapterZnp, ZNP_URL, 14),
]
FIXTURES = Path(__file__).parents[1] / "fixtures/crawler"


def fixture(nazwa):
    return (FIXTURES / nazwa / "cennik.html").read_text(encoding="utf-8")


def indeks(oferty):
    return {o.zrodlo_id: o for o in oferty}


@pytest.mark.parametrize(("nazwa", "klasa", "url", "liczba"), PRZYPADKI)
def test_rzeczywisty_cennik_ma_unikalne_poprawne_rekordy(nazwa, klasa, url, liczba):
    oferty = klasa().parsuj(fixture(nazwa), url)
    assert len(oferty) == len(indeks(oferty)) == liczba
    assert all(Oferta.model_validate_json(o.model_dump_json()) == o for o in oferty)
    assert all(isinstance(o.cena, Decimal) for o in oferty)
    assert all(o.dostepny is None and o.profile == [] for o in oferty)
    assert oferty == klasa().parsuj(fixture(nazwa), url)


def test_promien_rowspan_i_terminy_sa_przypisane_do_wlasciwych_cen():
    oferty = indeks(AdapterPromien().parsuj(fixture("promien"), PROMIEN_URL))
    oferta = oferty["turnus-14/dwojka/2026-09-17"]
    assert oferta.cena == Decimal("3920.00")
    assert oferta.termin_do == date(2026, 10, 1)
    assert oferta.liczba_dni == 14 and oferta.liczba_nocy is None
    assert oferta.jednostka_ceny == JednostkaCeny.TURNUS_OSOBA
    assert oferty["turnus-7/dwojka/2026-10-01"].cena == Decimal("1890.00")
    assert oferty["turnus-7/dwojka-plus/2026-10-01"].cena == Decimal("2100.00")
    assert oferty["turnus-14/apartament/2026-09-17"].cena == Decimal("4900.00")


def test_bristol_sezon_nie_jest_terminem_turnusu():
    oferty = indeks(AdapterBristol().parsuj(fixture("bristol"), BRISTOL_URL))
    oferta = oferty["sanatoryjny-2026/8-dni/dwojka/niski"]
    assert oferta.cena == Decimal("2086")
    assert (oferta.liczba_dni, oferta.liczba_nocy) == (8, 7)
    assert oferta.termin_od is None and oferta.termin_do is None
    assert "01.10.2026–21.12.2026" in oferta.nazwa_pakietu
    assert oferty["sanatoryjny-2026/8-dni/dostawka/wysoki"].cena == Decimal("1960")


def test_znp_apartament_i_cena_preferencyjna_nie_sa_przeliczane():
    oferty = AdapterZnp().parsuj(fixture("znp"), ZNP_URL)
    apartamenty = [o for o in oferty if o.typ_pokoju == TypPokoju.APARTAMENT]
    assert len(apartamenty) == 2
    assert {o.cena for o in apartamenty} == {Decimal("650"), Decimal("740")}
    assert all(o.jednostka_ceny == JednostkaCeny.POKOJ_DOBA for o in apartamenty)
    pakiety = [o for o in oferty if o.typ_pokoju == TypPokoju.DWUOSOBOWY and o.liczba_dni == 14]
    assert {o.cena for o in pakiety} == {Decimal("4270"), Decimal("4690")}
    assert Decimal("310") * 14 not in {o.cena for o in pakiety}
    assert all(o.termin_od is None and o.termin_do is None for o in oferty)


@pytest.mark.parametrize(
    ("nazwa", "klasa", "url", "stara", "nowa"),
    [
        ("promien", AdapterPromien, PROMIEN_URL, "3920,00", "3950,00"),
        ("bristol", AdapterBristol, BRISTOL_URL, "2086", "2099"),
        ("znp", AdapterZnp, ZNP_URL, "4 270,00", "4 290,00"),
    ],
)
def test_zmiana_ceny_nie_zmienia_id(nazwa, klasa, url, stara, nowa):
    html = fixture(nazwa)
    przed = indeks(klasa().parsuj(html, url))
    po = indeks(klasa().parsuj(html.replace(stara, nowa), url))
    assert przed.keys() == po.keys()
    assert any(przed[k].cena != po[k].cena for k in przed)


@pytest.mark.parametrize(("nazwa", "klasa", "url", "liczba"), PRZYPADKI)
def test_brak_ceny_jest_none_a_nie_zero(nazwa, klasa, url, liczba):
    soup = BeautifulSoup(fixture(nazwa), "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")
    row = rows[2] if nazwa == "promien" else rows[1] if nazwa == "bristol" else rows[4]
    cell = row.find_all("td", recursive=False)[-1]
    cell.clear()
    oferty = klasa().parsuj(str(soup), url)
    assert len(oferty) == liczba
    assert any(o.cena is None for o in oferty)


@pytest.mark.parametrize(("nazwa", "klasa", "url", "liczba"), PRZYPADKI)
def test_cena_od_nie_jest_cena_gwarantowana(nazwa, klasa, url, liczba):
    soup = BeautifulSoup(fixture(nazwa), "html.parser")
    rows = soup.find("table").find_all("tr")
    row = rows[2] if nazwa == "promien" else rows[1] if nazwa == "bristol" else rows[4]
    cell = row.find_all("td", recursive=False)[-1]
    cell.insert(0, "od ")
    assert any(o.cena_od for o in klasa().parsuj(str(soup), url))


@pytest.mark.parametrize(("nazwa", "klasa", "url", "liczba"), PRZYPADKI)
def test_zmieniony_html_nie_wyglada_jak_usuniecie_ofert(nazwa, klasa, url, liczba):
    with pytest.raises(ValueError):
        klasa().parsuj("<html><h1>Strona chwilowo niedostępna</h1></html>", url)


def test_brak_jednego_cennika_promienia_to_blad_czesciowego_pobrania():
    soup = BeautifulSoup(fixture("promien"), "html.parser")
    soup.find_all("table")[1].decompose()
    with pytest.raises(ValueError, match="obu cenników"):
        AdapterPromien().parsuj(str(soup), PROMIEN_URL)


def test_rejestr_zawiera_trzy_adaptery_produkcyjne():
    assert set(rejestr_produkcyjny().nazwy()) == {
        "sanatorium_promien",
        "sanatorium_bristol",
        "sanatorium_znp",
    }


@pytest.mark.parametrize(("nazwa", "klasa", "url", "liczba"), PRZYPADKI)
async def test_pelny_przebieg_i_powtorka_na_rzeczywistym_html(
    nazwa, klasa, url, liczba, tmp_path, monkeypatch
):
    async def bez_czekania(self, url):
        pass

    monkeypatch.setattr(Fetch, "_odczekaj", bez_czekania)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text=fixture(nazwa), headers={"content-type": "text/html"})

    raporty = []
    for _ in range(2):
        async with Fetch(
            user_agent="SanatoriaBot/1.0 (+https://test.example/bot; bot@test.example)",
            domeny=klasa.domeny,
            cache_dir=tmp_path / "cache",
            transport=httpx.MockTransport(handler),
        ) as fetch:
            raporty.append(await uruchom(klasa(), fetch, tmp_path / "out"))
    assert raporty[0]["kompletny"] is True
    assert raporty[0]["oferty_ok"] == liczba
    assert raporty[1]["zmiany"] == {"nowe": 0, "zmienione": 0, "zniknely": 0}
    plik = next((tmp_path / "out" / klasa.nazwa).glob("*.raport.json"))
    assert json.loads(plik.read_text(encoding="utf-8"))["oferty_odrzucone"] == 0
