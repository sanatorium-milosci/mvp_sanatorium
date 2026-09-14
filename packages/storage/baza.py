"""Zarządzanie połączeniem i cyklem życia bazy danych SQLite."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DOMYSLNA_SCIEZKA_BAZY = Path("dane/sanatoria.db")
SCIEZKA_SCHEMATU = Path(__file__).parent / "schemat.sql"


class BazaDanych:
    """Zarządca połączenia do bazy SQLite z obsługą trybu WAL i transakcji."""

    def __init__(self, sciezka: Path | str | None = None) -> None:
        if sciezka is None or sciezka == ":memory:":
            self.sciezka = Path(":memory:") if sciezka == ":memory:" else DOMYSLNA_SCIEZKA_BAZY
        else:
            self.sciezka = Path(sciezka)
        self._pamiec_conn: sqlite3.Connection | None = None
        if str(self.sciezka) == ":memory:":
            self._pamiec_conn = sqlite3.connect(":memory:", timeout=10.0, check_same_thread=False)
            self._pamiec_conn.row_factory = sqlite3.Row
            self._pamiec_conn.execute("PRAGMA foreign_keys = ON;")
        self.inicjalizuj()

    def inicjalizuj(self) -> None:
        """Tworzy katalog bazy i uruchamia migrację schematu."""
        if str(self.sciezka) != ":memory:":
            self.sciezka.parent.mkdir(parents=True, exist_ok=True)
        with self.polaczenie() as conn:
            conn.executescript(SCIEZKA_SCHEMATU.read_text(encoding="utf-8"))

    @contextmanager
    def polaczenie(self) -> Iterator[sqlite3.Connection]:
        """Udostępnia skonfigurowane połączenie z automatycznym commitem/rollbackiem."""
        if self._pamiec_conn is not None:
            with self._pamiec_conn:
                yield self._pamiec_conn
            return

        conn = sqlite3.connect(str(self.sciezka), timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def wykonaj_kopie_zapasowa(self, sciezka_kopii: Path | str) -> None:
        """Tworzy atomową kopię zapasową bazy SQLite do pliku docelowego."""
        cel = Path(sciezka_kopii)
        cel.parent.mkdir(parents=True, exist_ok=True)
        with self.polaczenie() as conn:
            kopia = sqlite3.connect(str(cel))
            try:
                conn.backup(kopia)
            finally:
                kopia.close()
