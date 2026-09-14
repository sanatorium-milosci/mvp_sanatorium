"""Narzędzia do jawnych tabel cenowych; bez domyślania brakujących komórek."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from decimal import Decimal

from bs4 import Tag

from packages.crawler.baza import parsuj_cene


def tekst(element: Tag) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def slug(wartosc: str) -> str:
    wartosc = unicodedata.normalize("NFKD", wartosc.lower().replace("ł", "l"))
    ascii_tekst = wartosc.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_tekst).strip("-")


def siatka(tabela: Tag) -> list[list[Tag]]:
    """Rozwiń rowspan/colspan, zachowując referencje do faktycznych komórek."""
    zajete: dict[tuple[int, int], Tag] = {}
    wynik = []
    for nr, wiersz in enumerate(tabela.find_all("tr")):
        kolumna = 0
        for komorka in wiersz.find_all(["td", "th"], recursive=False):
            while (nr, kolumna) in zajete:
                kolumna += 1
            szerokosc = int(komorka.get("colspan", 1))
            wysokosc = int(komorka.get("rowspan", 1))
            if not 1 <= szerokosc <= 50 or not 1 <= wysokosc <= 500:
                raise ValueError("Nieprawidłowy rozmiar scalonej komórki")
            for r in range(nr, nr + wysokosc):
                for c in range(kolumna, kolumna + szerokosc):
                    if (r, c) in zajete:
                        raise ValueError("Nakładające się komórki tabeli")
                    zajete[r, c] = komorka
            kolumna += szerokosc
        kolumny = sorted(c for r, c in zajete if r == nr)
        if kolumny != list(range(len(kolumny))):
            raise ValueError("Luka w strukturze tabeli")
        wynik.append([zajete[nr, c] for c in kolumny])
    if any(r >= len(wynik) for r, _ in zajete):
        raise ValueError("Rowspan wykracza poza tabelę")
    return wynik


def cena_komorki(komorka: Tag) -> Decimal | None:
    wartosc = tekst(komorka)
    if wartosc.casefold() in {"", "-", "–", "—", "brak ceny", "na zapytanie"}:
        return None
    return parsuj_cene(wartosc)


def zakresy_dat(wartosc: str, rok: int) -> list[tuple[date, date]]:
    wzor = r"(\d{2})\.(\d{2})\s*[-–—]\s*(\d{2})\.(\d{2})(?:\.(\d{4}))?"
    dopasowania = list(re.finditer(wzor, wartosc))
    reszta = re.sub(wzor, "", wartosc)
    reszta = re.sub(r"\b(?:oraz|r)\b|[.\s]", "", reszta, flags=re.IGNORECASE)
    if not dopasowania or reszta:
        raise ValueError("Nierozpoznany zapis terminów")
    wynik = []
    for m in dopasowania:
        d1, m1, d2, m2, podany_rok = m.groups()
        if podany_rok and int(podany_rok) != rok:
            raise ValueError("Rok terminu nie zgadza się z rokiem cennika")
        poczatek, koniec = date(rok, int(m1), int(d1)), date(rok, int(m2), int(d2))
        if koniec <= poczatek:
            raise ValueError("Koniec terminu nie jest późniejszy niż początek")
        wynik.append((poczatek, koniec))
    return wynik


def etykieta_okresow(okresy: list[tuple[date, date]]) -> str:
    return "; ".join(f"{od:%d.%m.%Y}–{do:%d.%m.%Y}" for od, do in okresy)
