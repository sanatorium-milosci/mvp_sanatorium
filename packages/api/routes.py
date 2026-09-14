"""Trasy endpointów REST API dla wyszukiwarki sanatoriów."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from packages.api.modele import (
    FiltryMetadaneDTO,
    ListaOfertOdpowiedzDTO,
    OfertaSzczegolyDTO,
    StronicowanieDTO,
    ZdrowieOdpowiedzDTO,
    buduj_oferte_dto,
    oblicz_strony,
)
from packages.api.zaleznosci import RepoDep
from packages.core.models import WERSJA_KONTRAKTU
from packages.storage.repozytorium import FiltryOfert

router = APIRouter(tags=["oferty"])


@router.get("/oferty", response_model=ListaOfertOdpowiedzDTO)
def pobierz_oferty(
    repo: RepoDep,
    q: Annotated[
        str | None, Query(description="Wyszukiwanie tekstowe w nazwie i miejscowości")
    ] = None,
    miejscowosc: Annotated[str | None, Query(description="Filtr miejscowości")] = None,
    wojewodztwo: Annotated[str | None, Query(description="Filtr województwa")] = None,
    profil: Annotated[str | None, Query(description="Profil leczniczy")] = None,
    wyzywienie: Annotated[str | None, Query(description="Standard wyżywienia")] = None,
    typ_pokoju: Annotated[str | None, Query(description="Typ pokoju")] = None,
    jednostka_ceny: Annotated[str | None, Query(description="Jednostka ceny")] = None,
    cena_min: Annotated[Decimal | None, Query(description="Minimalna cena")] = None,
    cena_max: Annotated[Decimal | None, Query(description="Maksymalna cena")] = None,
    min_dni: Annotated[int | None, Query(ge=1, description="Minimalna liczba dni")] = None,
    max_dni: Annotated[int | None, Query(ge=1, description="Maksymalna liczba dni")] = None,
    termin_od: Annotated[
        date | None, Query(description="Początek zakresu terminu (YYYY-MM-DD)")
    ] = None,
    termin_do: Annotated[
        date | None, Query(description="Koniec zakresu terminu (YYYY-MM-DD)")
    ] = None,
    tylko_dostepne: Annotated[bool, Query(description="Tylko oferty z wolnymi miejscami")] = False,
    basen: Annotated[bool | None, Query(description="Wymóg basenu")] = None,
    winda: Annotated[bool | None, Query(description="Wymóg windy")] = None,
    parking: Annotated[bool | None, Query(description="Wymóg parkingu")] = None,
    zwierzeta: Annotated[bool | None, Query(description="Możliwość zabrania zwierząt")] = None,
    dostepny_dla_wozka: Annotated[
        bool | None, Query(description="Dostępność dla osób na wózkach")
    ] = None,
    sortuj: Annotated[str, Query(description="Opcja sortowania")] = "najnowsze",
    pokaz_przeszle: Annotated[bool, Query(description="Czy pokazywać zakończone turnusy")] = False,
    strona: Annotated[int, Query(ge=1, description="Numer strony")] = 1,
    na_stronie: Annotated[int, Query(ge=1, le=100, description="Liczba ofert na stronę")] = 20,
) -> ListaOfertOdpowiedzDTO:
    """Wyszukuje i filtruje oferty komercyjnych pobytów sanatoryjnych."""
    if termin_od and termin_do and termin_do < termin_od:
        raise HTTPException(
            status_code=400,
            detail="termin_do nie może być wcześniejszy niż termin_od",
        )

    filtry = FiltryOfert(
        q=q,
        miejscowosc=miejscowosc,
        wojewodztwo=wojewodztwo,
        profil=profil,
        wyzywienie=wyzywienie,
        typ_pokoju=typ_pokoju,
        jednostka_ceny=jednostka_ceny,
        cena_min=cena_min,
        cena_max=cena_max,
        min_dni=min_dni,
        max_dni=max_dni,
        termin_od=termin_od,
        termin_do=termin_do,
        tylko_dostepne=tylko_dostepne,
        basen=basen,
        winda=winda,
        parking=parking,
        zwierzeta=zwierzeta,
        dostepny_dla_wozka=dostepny_dla_wozka,
        sortuj=sortuj,
        strona=strona,
        na_stronie=na_stronie,
        tylko_aktywne=True,
        tylko_przyszle=not pokaz_przeszle,
    )

    elementy_raw, razem = repo.szukaj_ofert(filtry)
    elementy = [buduj_oferte_dto(e) for e in elementy_raw]

    return ListaOfertOdpowiedzDTO(
        elementy=elementy,
        stronicowanie=StronicowanieDTO(
            strona=strona,
            na_stronie=na_stronie,
            razem=razem,
            stron_razem=oblicz_strony(razem, na_stronie),
        ),
    )


@router.get("/oferty/{oferta_id}", response_model=OfertaSzczegolyDTO)
def pobierz_szczegoly_oferty(oferta_id: int, repo: RepoDep) -> OfertaSzczegolyDTO:
    """Zwraca pełne szczegóły pojedynczej oferty."""
    oferta = repo.pobierz_oferte_po_id(oferta_id)
    if oferta is None:
        raise HTTPException(
            status_code=404,
            detail="Oferta o podanym ID nie została znaleziona",
        )
    return buduj_oferte_dto(oferta)


@router.get("/filtry", response_model=FiltryMetadaneDTO)
def pobierz_metadane_filtrow(repo: RepoDep) -> FiltryMetadaneDTO:
    """Zwraca aktualnie dostępne warianty filtrów na podstawie aktywnych ofert."""
    dane = repo.pobierz_filtry_metadane()
    return FiltryMetadaneDTO(**dane)


@router.get("/zdrowie", response_model=ZdrowieOdpowiedzDTO)
def sprawdz_zdrowie(repo: RepoDep) -> ZdrowieOdpowiedzDTO:
    """Status zdrowia API, bazy danych i ostatniego importu."""
    baza_ok = True
    try:
        aktywne = repo.policz_aktywne_oferty()
    except Exception:
        baza_ok = False
        aktywne = 0

    ostatni = repo.pobierz_ostatni_przebieg()
    ostatni_import = ostatni.get("zaimportowano_o") if ostatni else None

    return ZdrowieOdpowiedzDTO(
        status="ok" if baza_ok else "blad",
        wersja_api="0.1.0",
        wersja_kontraktu=WERSJA_KONTRAKTU,
        baza_ok=baza_ok,
        aktywne_oferty=aktywne,
        ostatni_import=ostatni_import,
    )
