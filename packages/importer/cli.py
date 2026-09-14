"""CLI do uruchamiania procesu importu JSONL."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from packages.importer.procesor import importuj_adapter, importuj_wszystkie
from packages.storage.baza import DOMYSLNA_SCIEZKA_BAZY, BazaDanych
from packages.storage.repozytorium import RepozytoriumOfert


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Importer danych JSONL zebranych przez crawlery do bazy ofert sanatoryjnych."
    )
    parser.add_argument(
        "--katalog",
        type=Path,
        default=Path("out"),
        help="Ścieżka do katalogu out z danymi crawlerów (domyślnie: out/)",
    )
    parser.add_argument(
        "--baza",
        type=Path,
        default=DOMYSLNA_SCIEZKA_BAZY,
        help="Ścieżka do pliku bazy SQLite (domyślnie: dane/sanatoria.db)",
    )
    parser.add_argument(
        "--adapter",
        type=str,
        default=None,
        help="Opcjonalna nazwa konkretnego adaptera do zaimportowania (np. demo)",
    )

    args = parser.parse_args()
    baza = BazaDanych(args.baza)
    repo = RepozytoriumOfert(baza)

    if args.adapter:
        sciezka_adaptera = args.katalog / args.adapter
        wynik = importuj_adapter(sciezka_adaptera, repo)
        if wynik.get("status") == "blad":
            sys.exit(1)
    else:
        wyniki = importuj_wszystkie(args.katalog, repo)
        if any(w.get("status") == "blad" for w in wyniki):
            sys.exit(1)


if __name__ == "__main__":
    main()
