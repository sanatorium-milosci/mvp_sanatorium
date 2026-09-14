"""Modele Pydantic reprezentujące dane zwracane przez API."""

from __future__ import annotations

import math
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from packages.api.kalkulator_ceny import oblicz_szacowany_koszt


class OsrodekDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    klucz: str
    nazwa: str
    miejscowosc: str
    wojewodztwo: str | None = None
    nip: str | None = None
    telefon: str | None = None


class PakietDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nazwa: str
    liczba_dni: int | None = None
    liczba_nocy: int | None = None
    termin_od: date | None = None
    termin_do: date | None = None
    dostepny: bool | None = None


class CenaDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wartosc: str | None = None
    waluta: str = "PLN"
    jednostka: str | None = None
    cena_od: bool = False
    szacowany_koszt_calkowity: str | None = None
    doplata_jedynka: str | None = None
    oplata_klimatyczna_doba: str | None = None


class StandardDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wyzywienie: str | None = None
    typ_pokoju: str | None = None
    liczba_zabiegow_dziennie: int | None = None
    zabiegi: list[str] = Field(default_factory=list)
    opieka_lekarska: bool | None = None


class UdogodnieniaDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    winda: bool | None = None
    dostepny_dla_wozka: bool | None = None
    parking: bool | None = None
    parking_platny: bool | None = None
    wifi: bool | None = None
    basen: bool | None = None
    zwierzeta: bool | None = None
    odleglosc_od_centrum_m: int | None = None


class LinkiDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url_rezerwacji: str | None = None
    url_zrodla: str
    pobrano_o: str


class OfertaSzczegolyDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    adapter: str
    zrodlo_id: str
    osrodek: OsrodekDTO
    pakiet: PakietDTO
    cena: CenaDTO
    standard: StandardDTO
    profile: list[str] = Field(default_factory=list)
    udogodnienia: UdogodnieniaDTO
    linki: LinkiDTO


class StronicowanieDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    strona: int
    na_stronie: int
    razem: int
    stron_razem: int


class ListaOfertOdpowiedzDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    elementy: list[OfertaSzczegolyDTO]
    stronicowanie: StronicowanieDTO


class FiltryMetadaneDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    miejscowosci: list[str]
    wojewodztwa: list[str]
    profile: list[str]
    wyzywienie: list[str]
    typy_pokoju: list[str]
    jednostki_ceny: list[str]
    cena_min: str | None = None
    cena_max: str | None = None
    min_dni: int | None = None
    max_dni: int | None = None
    liczba_ofert_razem: int


class ZdrowieOdpowiedzDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str
    wersja_api: str
    wersja_kontraktu: str
    baza_ok: bool
    aktywne_oferty: int
    ostatni_import: str | None = None


def buduj_oferte_dto(dane: dict[str, Any]) -> OfertaSzczegolyDTO:
    """Konwertuje słownik rekordu z repozytorium na strukturę OfertaSzczegolyDTO."""
    szacowany = oblicz_szacowany_koszt(
        cena=dane.get("cena"),
        jednostka_ceny=dane.get("jednostka_ceny"),
        liczba_dni=dane.get("liczba_dni"),
        liczba_nocy=dane.get("liczba_nocy"),
        termin_od=dane.get("termin_od"),
        termin_do=dane.get("termin_do"),
    )

    return OfertaSzczegolyDTO(
        id=dane["id"],
        adapter=dane["adapter"],
        zrodlo_id=dane["zrodlo_id"],
        osrodek=OsrodekDTO(
            klucz=dane["osrodek_klucz"],
            nazwa=dane["osrodek_nazwa"],
            miejscowosc=dane["miejscowosc"],
            wojewodztwo=dane.get("wojewodztwo"),
            nip=dane.get("nip"),
            telefon=dane.get("telefon"),
        ),
        pakiet=PakietDTO(
            nazwa=dane["nazwa_pakietu"],
            liczba_dni=dane.get("liczba_dni"),
            liczba_nocy=dane.get("liczba_nocy"),
            termin_od=dane.get("termin_od"),
            termin_do=dane.get("termin_do"),
            dostepny=dane.get("dostepny"),
        ),
        cena=CenaDTO(
            wartosc=dane.get("cena"),
            waluta=dane.get("waluta", "PLN"),
            jednostka=dane.get("jednostka_ceny"),
            cena_od=bool(dane.get("cena_od", False)),
            szacowany_koszt_calkowity=szacowany,
            doplata_jedynka=dane.get("doplata_jedynka"),
            oplata_klimatyczna_doba=dane.get("oplata_klimatyczna_doba"),
        ),
        standard=StandardDTO(
            wyzywienie=dane.get("wyzywienie"),
            typ_pokoju=dane.get("typ_pokoju"),
            liczba_zabiegow_dziennie=dane.get("liczba_zabiegow_dziennie"),
            zabiegi=dane.get("zabiegi", []),
            opieka_lekarska=dane.get("opieka_lekarska"),
        ),
        profile=dane.get("profile", []),
        udogodnienia=UdogodnieniaDTO(**(dane.get("udogodnienia") or {})),
        linki=LinkiDTO(
            url_rezerwacji=dane.get("url_rezerwacji"),
            url_zrodla=dane["zrodlo_url"],
            pobrano_o=dane["pobrano_o"],
        ),
    )


def oblicz_strony(razem: int, na_stronie: int) -> int:
    """Zwraca łączną liczbę stron."""
    if na_stronie <= 0:
        return 1
    return max(1, math.ceil(razem / na_stronie))
