"""Procesor importu danych z plików JSONL do bazy ofert."""

from __future__ import annotations

import logging
from pathlib import Path

from packages.core.models import Oferta
from packages.importer.walidator import sprawdz_gotowosc_do_importu
from packages.storage.repozytorium import RepozytoriumOfert

logger = logging.getLogger(__name__)


def importuj_adapter(katalog_adaptera: Path, repo: RepozytoriumOfert) -> dict:
    """
    Importuje oferty z katalogu pojedynczego adaptera.
    Gwarantuje, że importowane są tylko kompletne przebiegi, a zniknięte oferty
    są wycofywane bez usuwania danych w przypadku awarii.
    """
    gotowy, komunikat, raport, plik_jsonl = sprawdz_gotowosc_do_importu(katalog_adaptera)
    if not gotowy or plik_jsonl is None or raport is None:
        logger.warning(
            "Pominięto import adaptera %s: %s",
            katalog_adaptera.name,
            komunikat,
        )
        return {
            "status": "pominieto",
            "adapter": katalog_adaptera.name,
            "komunikat": komunikat,
        }

    adapter = raport.get("adapter", katalog_adaptera.name)
    oferty: list[Oferta] = []
    linie = plik_jsonl.read_text(encoding="utf-8").splitlines()
    for nr, linia in enumerate(linie, start=1):
        linia = linia.strip()
        if not linia:
            continue
        try:
            oferty.append(Oferta.model_validate_json(linia))
        except Exception as exc:
            logger.error(
                "Błąd walidacji wiersza %d w %s: %s",
                nr,
                plik_jsonl,
                exc,
            )
            return {
                "status": "blad",
                "adapter": adapter,
                "komunikat": f"Uszkodzony wiersz {nr} w {plik_jsonl.name}: {exc}",
            }

    # Upsert ofert w bazie
    statystyki = repo.upsert_oferty(adapter, oferty, oznacz_brakujace_nieaktywne=True)
    repo.zapisz_przebieg(raport)

    logger.info(
        "Zaimportowano adapter %s: %d ofert (nowe: %d, zaktualizowane: %d, wycofane: %d)",
        adapter,
        len(oferty),
        statystyki["dodane"],
        statystyki["zaktualizowane"],
        statystyki["dezaktywowane"],
    )

    return {
        "status": "sukces",
        "adapter": adapter,
        "zaimportowano": len(oferty),
        "statystyki": statystyki,
    }


def importuj_wszystkie(katalog_out: Path, repo: RepozytoriumOfert) -> list[dict]:
    """Przeszukuje katalog wyjściowy i importuje wszystkie znalezione podkatalogi adapterów."""
    wyniki = []
    if not katalog_out.exists():
        logger.warning("Katalog danych wyjściowych nie istnieje: %s", katalog_out)
        return wyniki

    for podkatalog in sorted(katalog_out.iterdir()):
        if podkatalog.is_dir() and not podkatalog.name.startswith((".", "_")):
            wynik = importuj_adapter(podkatalog, repo)
            wyniki.append(wynik)

    return wyniki
