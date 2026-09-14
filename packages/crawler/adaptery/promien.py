"""Terminy i ceny turnusów Sanatorium Promień w Ciechocinku."""

import re

from bs4 import BeautifulSoup

from packages.core.models import JednostkaCeny, Oferta, TypPokoju
from packages.crawler.adaptery.tabele import cena_komorki, siatka, tekst, zakresy_dat
from packages.crawler.baza import zrodlo_fragmentu
from packages.crawler.fetch import Fetch

URL = "https://www.sanatoriumpromien.pl/cennik-pobytow-pelnoplatnych"
POKOJE = {
    "1-osobowym": ("jedynka", TypPokoju.JEDNOOSOBOWY),
    "2-osobowym": ("dwojka", TypPokoju.DWUOSOBOWY),
    "2-osobowym podwyższony standard": ("dwojka-plus", TypPokoju.DWUOSOBOWY),
    "2-osobowym apartament": ("apartament", TypPokoju.APARTAMENT),
}


class AdapterPromien:
    nazwa = "sanatorium_promien"
    wersja = "1.0.0"
    domeny = ["www.sanatoriumpromien.pl", "sanatoriumpromien.pl"]
    wymaga_js = False

    async def zbierz_urle(self, fetch: Fetch) -> list[str]:
        return [URL]

    def parsuj(self, html: str, url: str) -> list[Oferta]:
        soup = BeautifulSoup(html, "html.parser")
        oferty = []
        dlugosci = set()
        for tabela in soup.select("table.cennik"):
            wiersze = siatka(tabela)
            if not wiersze:
                continue
            naglowek = tekst(wiersze[0][0])
            m = re.fullmatch(
                r"CENNIK (\d+) DNIOWYCH TURNUSÓW PEŁNOPŁATNYCH "
                r'W SANATORIUM "PROMIEŃ" NA ROK (\d{4})',
                naglowek,
                flags=re.IGNORECASE,
            )
            if not m:
                raise ValueError("Nierozpoznany nagłówek cennika Promienia")
            dni, rok = map(int, m.groups())
            if dni not in {7, 14} or dni in dlugosci:
                raise ValueError("Nieoczekiwany lub powtórzony rodzaj turnusu")
            dlugosci.add(dni)
            if [tekst(c) for c in wiersze[1]] != [
                "Termin turnusu",
                "Miejsce w pokoju",
                "Cena turnusu",
            ]:
                raise ValueError("Zmienione kolumny cennika Promienia")
            if len(wiersze) <= 2:
                raise ValueError("Pusty cennik Promienia")
            for wiersz in wiersze[2:]:
                if len(wiersz) != 3:
                    raise ValueError("Nieprawidłowy wiersz cennika Promienia")
                termin, pokoj, cena = wiersz
                nazwa_pokoju = tekst(pokoj).lower()
                if nazwa_pokoju not in POKOJE:
                    raise ValueError("Nowy rodzaj pokoju wymaga mapowania")
                pokoj_id, typ = POKOJE[nazwa_pokoju]
                for od, do in zakresy_dat(tekst(termin), rok):
                    oferty.append(
                        Oferta(
                            adapter=self.nazwa,
                            zrodlo_id=f"turnus-{dni}/{pokoj_id}/{od.isoformat()}",
                            osrodek_klucz="sanatorium-promien-ciechocinek",
                            osrodek_nazwa="Sanatorium Uzdrowiskowe „Promień”",
                            miejscowosc="Ciechocinek",
                            wojewodztwo="kujawsko-pomorskie",
                            nazwa_pakietu=f"Turnus {dni} dni — miejsce w pokoju {nazwa_pokoju}",
                            liczba_dni=dni,
                            termin_od=od,
                            termin_do=do,
                            cena=cena_komorki(cena),
                            cena_od=tekst(cena).casefold().startswith("od "),
                            jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
                            typ_pokoju=typ,
                            zrodlo=zrodlo_fragmentu(str(tabela), url, self.nazwa, self.wersja),
                        )
                    )
        if dlugosci != {7, 14}:
            raise ValueError("Nie znaleziono obu cenników turnusów Promienia")
        return oferty
