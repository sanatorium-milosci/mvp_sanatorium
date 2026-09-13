# packages/core/models.py  --- STREFA WSPÓLNA, zmiana tylko przez PR

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

WERSJA_KONTRAKTU = "0.1.0"


class ProfilLeczniczy(str, Enum):
    """Profile zgodne z nazewnictwem lecznictwa uzdrowiskowego NFZ."""

    ORTOPEDYCZNO_URAZOWY = "ortopedyczno_urazowy"
    REUMATOLOGICZNY = "reumatologiczny"
    KARDIOLOGICZNY = "kardiologiczny"
    NACZYN_OBWODOWYCH = "naczyn_obwodowych"
    GORNE_DROGI_ODDECHOWE = "gorne_drogi_oddechowe"
    DOLNE_DROGI_ODDECHOWE = "dolne_drogi_oddechowe"
    UKLAD_TRAWIENIA = "uklad_trawienia"
    ENDOKRYNOLOGICZNY = "endokrynologiczny"
    CUKRZYCA = "cukrzyca"
    OTYLOSC = "otylosc"
    OSTEOPOROZA = "osteoporoza"
    NEUROLOGICZNY = "neurologiczny"
    NERKI_DROGI_MOCZOWE = "nerki_drogi_moczowe"
    SKORA = "skora"
    KOBIECY = "kobiecy"
    PSYCHICZNY = "psychiczny"
    NIEZNANY = "nieznany"


class JednostkaCeny(str, Enum):
    OSOBODOBA = "osobodoba"  # cena za jedną osobę za dobę
    TURNUS_OSOBA = "turnus_osoba"  # cena za cały turnus za jedną osobę
    POKOJ_DOBA = "pokoj_doba"  # cena za pokój za dobę


class TypPokoju(str, Enum):
    JEDNOOSOBOWY = "jednoosobowy"
    DWUOSOBOWY = "dwuosobowy"
    APARTAMENT = "apartament"
    STUDIO = "studio"
    INNY = "inny"


class Wyzywienie(str, Enum):
    BRAK = "brak"
    SNIADANIA = "sniadania"
    HB = "hb"  # dwa posiłki
    FB = "fb"  # trzy posiłki
    ALL_INCLUSIVE = "all_inclusive"


class Zrodlo(BaseModel):
    """Skąd i kiedy pochodzi rekord. Wymagane dla każdej oferty."""

    url: HttpUrl
    pobrano_o: datetime
    adapter: str  # np. "uzdrowisko_ustron"
    wersja_adaptera: str  # semver, np. "1.2.0"
    hash_tresci: str  # sha256 fragmentu, z którego sparsowano ofertę


class Udogodnienia(BaseModel):
    """Wszystkie pola opcjonalne. None znaczy 'nie ustalono', nie 'nie ma'."""

    winda: bool | None = None
    dostepny_dla_wozka: bool | None = None
    parking: bool | None = None
    parking_platny: bool | None = None
    wifi: bool | None = None
    basen: bool | None = None
    zwierzeta: bool | None = None
    odleglosc_od_centrum_m: int | None = None


class Oferta(BaseModel):
    """
    Jedna oferta pobytu w jednym ośrodku.
    Jeśli ośrodek ma pięć pakietów, powstaje pięć rekordów Oferta.
    """

    # --- identyfikacja ---
    adapter: str
    zrodlo_id: str = Field(
        description="Stabilny klucz naturalny ze strony źródłowej. "
        "Jeśli strona nie ma id, użyj slug z URL. Musi być stabilny "
        "między przebiegami, inaczej wykrywanie zmian nie zadziała."
    )

    # --- ośrodek ---
    osrodek_klucz: str = Field(
        description="Slug ośrodka nadany przez adapter, np. 'uzdrowisko-ustron-rownica'. "
        "Ścieżka A dopasuje to do rekordu kanonicznego. "
        "Ma być stabilny, nie musi być globalnie unikalny."
    )
    osrodek_nazwa: str
    miejscowosc: str
    wojewodztwo: str | None = None
    nip: str | None = Field(
        default=None,
        description="Jeśli podany na stronie, np. w stopce. Bardzo pomaga w dopasowaniu.",
    )

    # --- pobyt ---
    nazwa_pakietu: str
    liczba_dni: int | None = None
    liczba_nocy: int | None = None
    termin_od: date | None = None
    termin_do: date | None = None
    dostepny: bool | None = Field(
        default=None, description="True jeśli strona jawnie pokazuje wolne miejsca."
    )

    # --- cena ---
    cena: Decimal | None = None
    jednostka_ceny: JednostkaCeny | None = None
    waluta: str = "PLN"
    cena_od: bool = Field(default=False, description="True, gdy strona podaje cenę 'od'.")

    # --- co w cenie ---
    wyzywienie: Wyzywienie | None = None
    typ_pokoju: TypPokoju | None = None
    doplata_jedynka: Decimal | None = None
    liczba_zabiegow_dziennie: int | None = None
    zabiegi: list[str] = Field(default_factory=list, description="Nazwy zabiegów, bez opisów.")
    opieka_lekarska: bool | None = None
    oplata_klimatyczna_doba: Decimal | None = None

    # --- klasyfikacja ---
    profile: list[ProfilLeczniczy] = Field(default_factory=list)

    # --- reszta ---
    udogodnienia: Udogodnienia = Field(default_factory=Udogodnienia)
    telefon: str | None = None
    url_rezerwacji: HttpUrl | None = None
    zrodlo: Zrodlo
