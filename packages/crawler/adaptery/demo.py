"""Adapter wyłącznie syntetycznej fixture. Nie jest adapterem realnego ośrodka."""

from selectolax.parser import HTMLParser

from packages.core.models import JednostkaCeny, Oferta, Wyzywienie
from packages.crawler.baza import parsuj_cene, zrodlo_fragmentu
from packages.crawler.fetch import Fetch

URL_DEMO = "https://sanatorium.example/oferty"


class AdapterDemo:
    nazwa = "demo"
    wersja = "0.1.0"
    domeny = ["sanatorium.example"]
    wymaga_js = False

    async def zbierz_urle(self, fetch: Fetch) -> list[str]:
        return [URL_DEMO]

    def parsuj(self, html: str, url: str) -> list[Oferta]:
        tabela = HTMLParser(html).css_first("table#oferty")
        if tabela is None:
            raise ValueError("Brak oczekiwanej tabeli ofert; sprawdź zmianę struktury strony")
        wynik = []
        for wiersz in tabela.css("tbody tr[data-id]"):
            pola = [komorka.text(strip=True) for komorka in wiersz.css("td")]
            if len(pola) != 5:
                raise ValueError("Nieprawidłowa liczba kolumn oferty")
            nazwa, dni, noce, cena, dostepnosc = pola
            wynik.append(
                Oferta(
                    adapter=self.nazwa,
                    zrodlo_id=wiersz.attributes["data-id"],
                    osrodek_klucz="sanatorium-demo",
                    osrodek_nazwa="Sanatorium demonstracyjne (dane fikcyjne)",
                    miejscowosc="Miejscowość testowa",
                    nazwa_pakietu=nazwa,
                    liczba_dni=int(dni) if dni else None,
                    liczba_nocy=int(noce) if noce else None,
                    cena=parsuj_cene(cena),
                    cena_od=cena.lower().startswith("od "),
                    jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
                    dostepny={"wolne miejsca": True, "wyprzedana": False}.get(dostepnosc),
                    wyzywienie=Wyzywienie.FB,
                    zrodlo=zrodlo_fragmentu(wiersz.html, url, self.nazwa, self.wersja),
                )
            )
        return wynik
