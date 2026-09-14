"""ZNP: osobodoby, pakiety za osobę i osobno doba całego apartamentu."""

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

URL = "https://znpciechocinek.pl/cennik/cennik-indywidualni/"
POKOJE = {
    "1-osobowym": ("jedynka", TypPokoju.JEDNOOSOBOWY),
    "2-osobowym": ("dwojka", TypPokoju.DWUOSOBOWY),
    "3-osobowym": ("trojka", TypPokoju.INNY),
    "Apartament – CAŁY": ("apartament-caly", TypPokoju.APARTAMENT),
}


class AdapterZnp:
    nazwa = "sanatorium_znp"
    wersja = "1.0.0"
    domeny = ["znpciechocinek.pl", "www.znpciechocinek.pl"]
    wymaga_js = False

    async def zbierz_urle(self, fetch: Fetch) -> list[str]:
        return [URL]

    def parsuj(self, html: str, url: str) -> list[Oferta]:
        soup = BeautifulSoup(html, "html.parser")
        tabele = [t for t in soup.find_all("table") if "Oferta cenowa na" in tekst(t)]
        if len(tabele) != 1:
            raise ValueError("Nie znaleziono jednoznacznego cennika ZNP")
        tabela = tabele[0]
        wiersze = siatka(tabela)
        if len(wiersze) < 5 or any(len(w) != 5 for w in wiersze):
            raise ValueError("Zmieniona struktura cennika ZNP")
        m = re.fullmatch(
            r"Oferta cenowa na (\d{4}) rok dla klientów indywidualnych", tekst(wiersze[0][0])
        )
        if not m:
            raise ValueError("Brak roku cennika ZNP")
        rok = int(m.group(1))
        if tekst(wiersze[1][0]) != "Miejsce w pokoju":
            raise ValueError("Nierozpoznana jednostka ceny ZNP")
        kolumny = []
        for nr in range(1, 5):
            okresy = zakresy_dat(tekst(wiersze[2][nr]), rok)
            naglowek = tekst(wiersze[3][nr])
            if naglowek == "Cena za dobę":
                dni = None
            elif m := re.fullmatch(r"Cena za turnus (\d+) dni\*", naglowek):
                dni = int(m.group(1))
            else:
                raise ValueError("Nieznana jednostka rozliczeniowa ZNP")
            kolumny.append((okresy, dni))
        wynik = []
        for wiersz in wiersze[4:]:
            pokoj = tekst(wiersz[0])
            if pokoj not in POKOJE:
                raise ValueError("Nowy rodzaj pokoju ZNP wymaga mapowania")
            pokoj_id, typ = POKOJE[pokoj]
            for komorka, (okresy, dni) in zip(wiersz[1:], kolumny, strict=True):
                caly_apartament = pokoj_id == "apartament-caly"
                if caly_apartament and dni is not None:
                    # Kontrakt 0.1.0 nie ma ceny całego pokoju za turnus.
                    # Nie wolno podmienić jej na cenę za osobę ani dzielić przez 14.
                    continue
                jednostka = (
                    JednostkaCeny.POKOJ_DOBA
                    if caly_apartament
                    else JednostkaCeny.TURNUS_OSOBA
                    if dni
                    else JednostkaCeny.OSOBODOBA
                )
                wariant = f"turnus-{dni}" if dni else "doba"
                pierwsza_data = min(od for od, _ in okresy)
                opis_pokoju = "cały apartament" if caly_apartament else "miejsce w pokoju " + pokoj
                wynik.append(
                    Oferta(
                        adapter=self.nazwa,
                        zrodlo_id=f"cennik-{rok}/{pierwsza_data:%m-%d}/{pokoj_id}/{wariant}",
                        osrodek_klucz="sanatorium-znp-ciechocinek",
                        osrodek_nazwa="Sanatorium Uzdrowiskowe ZNP",
                        miejscowosc="Ciechocinek",
                        wojewodztwo="kujawsko-pomorskie",
                        nazwa_pakietu=(
                            f"Pobyt pełnopłatny — {wariant.replace('-', ' ')} — "
                            f"{opis_pokoju}"
                            f" — taryfa {etykieta_okresow(okresy)}"
                        ),
                        liczba_dni=dni,
                        cena=cena_komorki(komorka),
                        cena_od=tekst(komorka).casefold().startswith("od "),
                        jednostka_ceny=jednostka,
                        typ_pokoju=typ,
                        zrodlo=zrodlo_fragmentu(str(tabela), url, self.nazwa, self.wersja),
                    )
                )
        return wynik
