"""Cennik pakietów Bristol; sezon cenowy nie jest terminem rezerwacji."""

import re

from bs4 import BeautifulSoup

from packages.core.models import JednostkaCeny, Oferta, TypPokoju
from packages.crawler.adaptery.tabele import (
    cena_komorki,
    etykieta_okresow,
    siatka,
    tekst,
    zakresy_dat,
)
from packages.crawler.baza import zrodlo_fragmentu
from packages.crawler.fetch import Fetch

URL = "https://sankud.pl/cennik-sanatoryjny/"
POKOJE = {
    "w pokoju 1-osobowym za 1 os.": ("jedynka", TypPokoju.JEDNOOSOBOWY, "pokój 1-osobowy"),
    "w pokoju 2-osobowym za 1 os.": ("dwojka", TypPokoju.DWUOSOBOWY, "pokój 2-osobowy"),
    "w apartamencie za os.": ("apartament", TypPokoju.APARTAMENT, "apartament"),
    "sanatoryjny prywatny na dostawce - za 1 os.": ("dostawka", TypPokoju.INNY, "dostawka"),
}
SEZONY = {"NISKI": "niski", "ŚREDNI": "sredni", "WYSOKI": "wysoki"}


class AdapterBristol:
    nazwa = "sanatorium_bristol"
    wersja = "1.0.0"
    domeny = ["sankud.pl", "www.sankud.pl"]
    wymaga_js = False

    async def zbierz_urle(self, fetch: Fetch) -> list[str]:
        return [URL]

    def parsuj(self, html: str, url: str) -> list[Oferta]:
        tabela = BeautifulSoup(html, "html.parser").select_one("table#tablepress-7")
        if tabela is None:
            raise ValueError("Brak tabeli pakietów Bristol")
        wiersze = siatka(tabela)
        if len(wiersze) < 2 or len(wiersze[0]) != 4:
            raise ValueError("Zmieniona struktura cennika Bristol")
        m = re.fullmatch(
            r"Cennik na (\d{4}) rok obowiązuje przy min\. (\d+)-dniowym \((\d+) noclegów\) pobycie",
            tekst(wiersze[0][0]),
        )
        if not m:
            raise ValueError("Nierozpoznany rok lub długość pobytu Bristol")
        rok, dni, noce = map(int, m.groups())
        sezony = []
        for kolumna in wiersze[0][1:]:
            m = re.fullmatch(r"SEZON (NISKI|ŚREDNI|WYSOKI) (.+)", tekst(kolumna))
            if not m:
                raise ValueError("Nierozpoznana taryfa sezonowa Bristol")
            etykieta, okresy = m.groups()
            sezony.append((SEZONY[etykieta], etykieta.lower(), zakresy_dat(okresy, rok)))
        if len({s[0] for s in sezony}) != 3:
            raise ValueError("Powtórzona taryfa sezonowa Bristol")
        wynik = []
        for wiersz in wiersze[1:]:
            if len(wiersz) != 4:
                raise ValueError("Nieprawidłowy wiersz Bristol")
            opis = tekst(wiersz[0])
            prefiks = f"{dni}-dniowy pobyt "
            if not opis.startswith(prefiks) or opis.removeprefix(prefiks) not in POKOJE:
                raise ValueError("Nierozpoznany pokój lub jednostka ceny Bristol")
            pokoj_id, typ, pokoj = POKOJE[opis.removeprefix(prefiks)]
            for komorka, (sezon_id, sezon, okresy) in zip(wiersz[1:], sezony, strict=True):
                wynik.append(
                    Oferta(
                        adapter=self.nazwa,
                        zrodlo_id=f"sanatoryjny-{rok}/{dni}-dni/{pokoj_id}/{sezon_id}",
                        osrodek_klucz="bristol-kudowa-zdroj",
                        osrodek_nazwa="Sanatorium Uzdrowiskowe „Bristol” MSWiA",
                        miejscowosc="Kudowa-Zdrój",
                        wojewodztwo="dolnośląskie",
                        nazwa_pakietu=(
                            f"Pobyt sanatoryjny {dni} dni / {noce} nocy — {pokoj} — "
                            f"sezon {sezon} ({etykieta_okresow(okresy)})"
                        ),
                        liczba_dni=dni,
                        liczba_nocy=noce,
                        cena=cena_komorki(komorka),
                        cena_od=tekst(komorka).casefold().startswith("od "),
                        jednostka_ceny=JednostkaCeny.TURNUS_OSOBA,
                        typ_pokoju=typ,
                        zrodlo=zrodlo_fragmentu(str(tabela), url, self.nazwa, self.wersja),
                    )
                )
        return wynik
