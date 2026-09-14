"""Walidacja gotowości katalogu wyjściowego crawlera do importu."""

from __future__ import annotations

import json
from pathlib import Path


def sprawdz_gotowosc_do_importu(
    katalog_adaptera: Path,
) -> tuple[bool, str, dict | None, Path | None]:
    """
    Weryfikuje, czy katalog adaptera jest gotowy do bezpiecznego importu:
    - Brak blokady .run.lock (crawler nie jest w trakcie zapisu),
    - Istnienie raportu YYYY-MM-DD.raport.json,
    - Flaga kompletny == True w raporcie (ochrona przed utratą danych po awarii),
    - Istnienie pliku danych YYYY-MM-DD.jsonl.
    """
    if not katalog_adaptera.exists() or not katalog_adaptera.is_dir():
        return False, f"Katalog nie istnieje: {katalog_adaptera}", None, None

    blokada = katalog_adaptera / ".run.lock"
    if blokada.exists():
        return False, f"Crawler w trakcie pracy (obecna blokada {blokada})", None, None

    # Wyszukanie najnowszego raportu
    raporty = sorted(katalog_adaptera.glob("*.raport.json"), reverse=True)
    if not raporty:
        return False, f"Brak raportów w katalogu {katalog_adaptera}", None, None

    najnowszy_raport = raporty[0]
    try:
        dane_raportu = json.loads(najnowszy_raport.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Niepoprawny plik raportu {najnowszy_raport}: {exc}", None, None

    if not dane_raportu.get("kompletny"):
        return (
            False,
            (
                f"Przebieg niekompletny (kompletny=false) w {najnowszy_raport.name} - "
                "import pominięty dla ochrony istniejących danych"
            ),
            dane_raportu,
            None,
        )

    # Odpowiadający plik JSONL (np. 2026-09-14.raport.json -> 2026-09-14.jsonl)
    nazwa_jsonl = najnowszy_raport.name.replace(".raport.json", ".jsonl")
    plik_jsonl = katalog_adaptera / nazwa_jsonl
    if not plik_jsonl.exists():
        return False, f"Brak pliku danych {plik_jsonl}", dane_raportu, None

    return True, "Gotowy do importu", dane_raportu, plik_jsonl
