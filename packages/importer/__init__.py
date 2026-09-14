"""Moduł bezpiecznego importu danych JSONL z crawlerów do bazy danych."""

from packages.importer.procesor import importuj_adapter, importuj_wszystkie
from packages.importer.walidator import sprawdz_gotowosc_do_importu

__all__ = ["importuj_adapter", "importuj_wszystkie", "sprawdz_gotowosc_do_importu"]
