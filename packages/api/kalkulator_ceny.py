"""Kalkulator szacowanego kosztu całkowitego pobytu.

Zasada kontraktu:
Brak danych oznacza „nie ustalono”. Nie zgadujemy dostępności, terminów ani kosztów.
Koszt całego pobytu oblicza backend tylko wtedy, gdy dane jednoznacznie na to pozwalają.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation


def oblicz_szacowany_koszt(
    cena: Decimal | str | float | None,
    jednostka_ceny: str | None,
    liczba_dni: int | None = None,
    liczba_nocy: int | None = None,
    termin_od: date | str | None = None,
    termin_do: date | str | None = None,
) -> str | None:
    """
    Oblicza szacowany koszt całkowity pobytu, jeśli dane są jednoznaczne.
    Zwraca kwotę jako string z 2 miejscami po przecinku, np. '1290.00', lub None.
    """
    if cena is None or str(cena).strip() == "":
        return None

    try:
        cena_dec = Decimal(str(cena))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if not cena_dec.is_finite() or cena_dec < 0:
        return None

    # Przypadek 1: Cena za cały turnus dla jednej osoby
    if jednostka_ceny == "turnus_osoba":
        return f"{cena_dec:.2f}"

    # Przypadek 2: Cena za osobodobę (wymaga jednoznacznej długości pobytu w dniach)
    if jednostka_ceny == "osobodoba":
        dni: int | None = None
        if liczba_dni is not None and liczba_dni > 0:
            dni = liczba_dni
        elif liczba_nocy is not None and liczba_nocy > 0:
            dni = liczba_nocy
        elif termin_od and termin_do:
            data_od = (
                date.fromisoformat(str(termin_od)) if isinstance(termin_od, str) else termin_od
            )
            data_do = (
                date.fromisoformat(str(termin_do)) if isinstance(termin_do, str) else termin_do
            )
            roznica = (data_do - data_od).days
            if roznica > 0:
                dni = roznica

        if dni is not None:
            return f"{cena_dec * dni:.2f}"
        return None

    # W każdym innym przypadku (np. pokoj_doba bez znajomości obłożenia lub brak jednostki):
    # Nie zgadujemy kosztu całkowitego dla pojedynczej osoby.
    return None
