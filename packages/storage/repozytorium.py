"""Warstwa repozytorium do zapisu, aktualizacji i wyszukiwania ofert sanatoryjnych."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from packages.core.models import Oferta
from packages.storage.baza import BazaDanych


@dataclass
class FiltryOfert:
    """Kryteria filtrowania i stronicowania dla wyszukiwarki ofert."""

    q: str | None = None
    miejscowosc: str | None = None
    wojewodztwo: str | None = None
    profil: str | None = None
    wyzywienie: str | None = None
    typ_pokoju: str | None = None
    jednostka_ceny: str | None = None
    cena_min: Decimal | None = None
    cena_max: Decimal | None = None
    min_dni: int | None = None
    max_dni: int | None = None
    termin_od: date | None = None
    termin_do: date | None = None
    tylko_dostepne: bool = False
    basen: bool | None = None
    winda: bool | None = None
    parking: bool | None = None
    zwierzeta: bool | None = None
    dostepny_dla_wozka: bool | None = None
    sortuj: str = "najnowsze"
    strona: int = 1
    na_stronie: int = 20
    tylko_aktywne: bool = True
    tylko_przyszle: bool = True


def _wiersz_na_slownik(row: dict) -> dict:
    """Konwertuje wiersz z bazy danych na słownik z deserializowanymi polami JSON."""
    wynik = dict(row)
    wynik["zabiegi"] = json.loads(wynik.pop("zabiegi_json", "[]"))
    wynik["profile"] = json.loads(wynik.pop("profile_json", "[]"))
    wynik["udogodnienia"] = json.loads(wynik.pop("udogodnienia_json", "{}"))
    if wynik.get("dostepny") is not None:
        wynik["dostepny"] = bool(wynik["dostepny"])
    if wynik.get("opieka_lekarska") is not None:
        wynik["opieka_lekarska"] = bool(wynik["opieka_lekarska"])
    wynik["cena_od"] = bool(wynik.get("cena_od", 0))
    wynik["aktywna"] = bool(wynik.get("aktywna", 1))
    return wynik


class RepozytoriumOfert:
    """Repozytorium do zarządzania ofertami i historią przebiegów w SQLite."""

    def __init__(self, baza: BazaDanych) -> None:
        self.baza = baza

    def upsert_oferty(
        self,
        adapter: str,
        oferty: list[Oferta],
        *,
        oznacz_brakujace_nieaktywne: bool = True,
    ) -> dict[str, int]:
        """
        Zapisuje lub aktualizuje oferty danego adaptera.
        W przypadku kompletnego przebiegu oferty nieobecne w nowej paczce
        są oznaczane jako nieaktywne (bez ich usuwania z historii).
        """
        teraz = datetime.now(UTC).isoformat()
        dodane = 0
        zaktualizowane = 0
        dezaktywowane = 0

        with self.baza.polaczenie() as conn:
            # 1. Sprawdzenie istniejących ofert dla tego adaptera
            kursor = conn.execute(
                "SELECT zrodlo_id FROM oferty WHERE adapter = ?",
                (adapter,),
            )
            istniejace_ids = {wiersz["zrodlo_id"] for wiersz in kursor.fetchall()}
            nowe_ids = {o.zrodlo_id for o in oferty}

            # 2. Opcjonalna dezaktywacja znikniętych ofert
            if oznacz_brakujace_nieaktywne:
                brakujace = istniejace_ids - nowe_ids
                if brakujace:
                    placeholders = ",".join("?" for _ in brakujace)
                    wynik = conn.execute(
                        f"""
                        UPDATE oferty
                        SET aktywna = 0, zaktualizowano_o = ?
                        WHERE adapter = ? AND zrodlo_id IN ({placeholders}) AND aktywna = 1
                        """,
                        [teraz, adapter, *brakujace],
                    )
                    dezaktywowane = wynik.rowcount

            # 3. Wstawianie lub aktualizowanie ofert
            zapytanie_upsert = """
                INSERT INTO oferty (
                    adapter, zrodlo_id, osrodek_klucz, osrodek_nazwa, miejscowosc, wojewodztwo, nip,
                    nazwa_pakietu, liczba_dni, liczba_nocy, termin_od, termin_do, dostepny,
                    cena, jednostka_ceny, waluta, cena_od, wyzywienie, typ_pokoju,
                    doplata_jedynka, liczba_zabiegow_dziennie, zabiegi_json,
                    opieka_lekarska, oplata_klimatyczna_doba, profile_json, udogodnienia_json,
                    telefon, url_rezerwacji, zrodlo_url, pobrano_o, wersja_adaptera, hash_tresci,
                    aktywna, utworzono_o, zaktualizowano_o
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    1, ?, ?
                )
                ON CONFLICT(adapter, zrodlo_id) DO UPDATE SET
                    osrodek_klucz = excluded.osrodek_klucz,
                    osrodek_nazwa = excluded.osrodek_nazwa,
                    miejscowosc = excluded.miejscowosc,
                    wojewodztwo = excluded.wojewodztwo,
                    nip = excluded.nip,
                    nazwa_pakietu = excluded.nazwa_pakietu,
                    liczba_dni = excluded.liczba_dni,
                    liczba_nocy = excluded.liczba_nocy,
                    termin_od = excluded.termin_od,
                    termin_do = excluded.termin_do,
                    dostepny = excluded.dostepny,
                    cena = excluded.cena,
                    jednostka_ceny = excluded.jednostka_ceny,
                    waluta = excluded.waluta,
                    cena_od = excluded.cena_od,
                    wyzywienie = excluded.wyzywienie,
                    typ_pokoju = excluded.typ_pokoju,
                    doplata_jedynka = excluded.doplata_jedynka,
                    liczba_zabiegow_dziennie = excluded.liczba_zabiegow_dziennie,
                    zabiegi_json = excluded.zabiegi_json,
                    opieka_lekarska = excluded.opieka_lekarska,
                    oplata_klimatyczna_doba = excluded.oplata_klimatyczna_doba,
                    profile_json = excluded.profile_json,
                    udogodnienia_json = excluded.udogodnienia_json,
                    telefon = excluded.telefon,
                    url_rezerwacji = excluded.url_rezerwacji,
                    zrodlo_url = excluded.zrodlo_url,
                    pobrano_o = excluded.pobrano_o,
                    wersja_adaptera = excluded.wersja_adaptera,
                    hash_tresci = excluded.hash_tresci,
                    aktywna = 1,
                    zaktualizowano_o = excluded.zaktualizowano_o
            """

            for oferta in oferty:
                wartosci = (
                    oferta.adapter,
                    oferta.zrodlo_id,
                    oferta.osrodek_klucz,
                    oferta.osrodek_nazwa,
                    oferta.miejscowosc,
                    oferta.wojewodztwo,
                    oferta.nip,
                    oferta.nazwa_pakietu,
                    oferta.liczba_dni,
                    oferta.liczba_nocy,
                    oferta.termin_od.isoformat() if oferta.termin_od else None,
                    oferta.termin_do.isoformat() if oferta.termin_do else None,
                    1 if oferta.dostepny is True else (0 if oferta.dostepny is False else None),
                    str(oferta.cena) if oferta.cena is not None else None,
                    oferta.jednostka_ceny.value if oferta.jednostka_ceny else None,
                    oferta.waluta,
                    1 if oferta.cena_od else 0,
                    oferta.wyzywienie.value if oferta.wyzywienie else None,
                    oferta.typ_pokoju.value if oferta.typ_pokoju else None,
                    str(oferta.doplata_jedynka) if oferta.doplata_jedynka is not None else None,
                    oferta.liczba_zabiegow_dziennie,
                    json.dumps(oferta.zabiegi, ensure_ascii=False),
                    1
                    if oferta.opieka_lekarska is True
                    else (0 if oferta.opieka_lekarska is False else None),
                    (
                        str(oferta.oplata_klimatyczna_doba)
                        if oferta.oplata_klimatyczna_doba is not None
                        else None
                    ),
                    json.dumps([p.value for p in oferta.profile], ensure_ascii=False),
                    oferta.udogodnienia.model_dump_json(),
                    oferta.telefon,
                    str(oferta.url_rezerwacji) if oferta.url_rezerwacji else None,
                    str(oferta.zrodlo.url),
                    oferta.zrodlo.pobrano_o.isoformat(),
                    oferta.zrodlo.wersja_adaptera,
                    oferta.zrodlo.hash_tresci,
                    teraz,
                    teraz,
                )
                conn.execute(zapytanie_upsert, wartosci)
                if oferta.zrodlo_id in istniejace_ids:
                    zaktualizowane += 1
                else:
                    dodane += 1

        return {
            "dodane": dodane,
            "zaktualizowane": zaktualizowane,
            "dezaktywowane": dezaktywowane,
        }

    def pobierz_oferte_po_id(self, oferta_id: int) -> dict | None:
        """Zwraca pojedynczą ofertę po kluczu głównym."""
        with self.baza.polaczenie() as conn:
            kursor = conn.execute("SELECT * FROM oferty WHERE id = ?", (oferta_id,))
            wiersz = kursor.fetchone()
            if wiersz is None:
                return None
            return _wiersz_na_slownik(dict(wiersz))

    def szukaj_ofert(self, filtry: FiltryOfert) -> tuple[list[dict], int]:
        """
        Wyszukuje oferty według kryteriów, zwraca krotkę (elementy, laczna_liczba_ofert).
        """
        warunki: list[str] = []
        parametry: list[object] = []

        if filtry.tylko_aktywne:
            warunki.append("aktywna = 1")

        if filtry.q:
            slowo = f"%{filtry.q.strip()}%"
            warunki.append("(nazwa_pakietu LIKE ? OR osrodek_nazwa LIKE ? OR miejscowosc LIKE ?)")
            parametry.extend([slowo, slowo, slowo])

        if filtry.miejscowosc:
            warunki.append("LOWER(miejscowosc) = LOWER(?)")
            parametry.append(filtry.miejscowosc.strip())

        if filtry.wojewodztwo:
            warunki.append("LOWER(wojewodztwo) = LOWER(?)")
            parametry.append(filtry.wojewodztwo.strip())

        if filtry.profil:
            # profile_json zawiera tablicę json stringów
            warunki.append("profile_json LIKE ?")
            parametry.append(f'%"{filtry.profil.strip()}"%')

        if filtry.wyzywienie:
            warunki.append("wyzywienie = ?")
            parametry.append(filtry.wyzywienie.strip())

        if filtry.typ_pokoju:
            warunki.append("typ_pokoju = ?")
            parametry.append(filtry.typ_pokoju.strip())

        if filtry.jednostka_ceny:
            warunki.append("jednostka_ceny = ?")
            parametry.append(filtry.jednostka_ceny.strip())

        if filtry.cena_min is not None:
            warunki.append("CAST(cena AS NUMERIC) >= ?")
            parametry.append(float(filtry.cena_min))

        if filtry.cena_max is not None:
            warunki.append("CAST(cena AS NUMERIC) <= ?")
            parametry.append(float(filtry.cena_max))

        if filtry.min_dni is not None:
            warunki.append("liczba_dni >= ?")
            parametry.append(filtry.min_dni)

        if filtry.max_dni is not None:
            warunki.append("liczba_dni <= ?")
            parametry.append(filtry.max_dni)

        if filtry.termin_od:
            warunki.append("(termin_od IS NULL OR termin_od >= ?)")
            parametry.append(filtry.termin_od.isoformat())

        if filtry.termin_do:
            warunki.append("(termin_do IS NULL OR termin_do <= ?)")
            parametry.append(filtry.termin_do.isoformat())

        if filtry.tylko_przyszle:
            dzisiaj = date.today().isoformat()
            warunki.append("(termin_do IS NULL OR termin_do >= ?)")
            parametry.append(dzisiaj)

        if filtry.tylko_dostepne:
            warunki.append("dostepny = 1")

        # Udogodnienia w formacie JSON
        for pole, wartosc in [
            ("basen", filtry.basen),
            ("winda", filtry.winda),
            ("parking", filtry.parking),
            ("zwierzeta", filtry.zwierzeta),
            ("dostepny_dla_wozka", filtry.dostepny_dla_wozka),
        ]:
            if wartosc is True:
                warunki.append(f'json_extract(udogodnienia_json, "$.{pole}") = 1')
            elif wartosc is False:
                warunki.append(f'json_extract(udogodnienia_json, "$.{pole}") = 0')

        klauzula_where = f"WHERE {' AND '.join(warunki)}" if warunki else ""

        # Mapowanie sortowania
        sortowania = {
            "cena_asc": "CAST(cena AS NUMERIC) ASC NULLS LAST",
            "cena_desc": "CAST(cena AS NUMERIC) DESC NULLS LAST",
            "dni_asc": "liczba_dni ASC NULLS LAST",
            "dni_desc": "liczba_dni DESC NULLS LAST",
            "termin_od_asc": "termin_od ASC NULLS LAST",
            "najnowsze": "id DESC",
        }
        order_by = sortowania.get(filtry.sortuj, "id DESC")

        na_stronie = max(1, min(filtry.na_stronie, 100))
        strona = max(1, filtry.strona)
        offset = (strona - 1) * na_stronie

        with self.baza.polaczenie() as conn:
            # Zliczenie wszystkich pasujących rekordów
            zapytanie_count = f"SELECT COUNT(*) as razem FROM oferty {klauzula_where}"
            razem = conn.execute(zapytanie_count, parametry).fetchone()["razem"]

            # Pobranie wybranej strony
            zapytanie_select = f"""
                SELECT * FROM oferty
                {klauzula_where}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """
            kursor = conn.execute(zapytanie_select, [*parametry, na_stronie, offset])
            elementy = [_wiersz_na_slownik(dict(r)) for r in kursor.fetchall()]

        return elementy, razem

    def pobierz_filtry_metadane(self) -> dict:
        """Zwraca unikalne wartości filtrów na podstawie aktywnych ofert w bazie."""
        with self.baza.polaczenie() as conn:
            miejscowosci = [
                r["miejscowosc"]
                for r in conn.execute(
                    "SELECT DISTINCT miejscowosc FROM oferty WHERE aktywna = 1 ORDER BY miejscowosc"
                ).fetchall()
                if r["miejscowosc"]
            ]
            wojewodztwa = [
                r["wojewodztwo"]
                for r in conn.execute(
                    "SELECT DISTINCT wojewodztwo FROM oferty "
                    "WHERE aktywna = 1 AND wojewodztwo IS NOT NULL ORDER BY wojewodztwo"
                ).fetchall()
                if r["wojewodztwo"]
            ]
            wyzywienie = [
                r["wyzywienie"]
                for r in conn.execute(
                    "SELECT DISTINCT wyzywienie FROM oferty "
                    "WHERE aktywna = 1 AND wyzywienie IS NOT NULL ORDER BY wyzywienie"
                ).fetchall()
                if r["wyzywienie"]
            ]
            typy_pokoju = [
                r["typ_pokoju"]
                for r in conn.execute(
                    "SELECT DISTINCT typ_pokoju FROM oferty "
                    "WHERE aktywna = 1 AND typ_pokoju IS NOT NULL ORDER BY typ_pokoju"
                ).fetchall()
                if r["typ_pokoju"]
            ]
            jednostki_ceny = [
                r["jednostka_ceny"]
                for r in conn.execute(
                    "SELECT DISTINCT jednostka_ceny FROM oferty "
                    "WHERE aktywna = 1 AND jednostka_ceny IS NOT NULL ORDER BY jednostka_ceny"
                ).fetchall()
                if r["jednostka_ceny"]
            ]

            zakresy = conn.execute(
                """
                SELECT
                    MIN(CAST(cena AS NUMERIC)) as cena_min,
                    MAX(CAST(cena AS NUMERIC)) as cena_max,
                    MIN(liczba_dni) as min_dni,
                    MAX(liczba_dni) as max_dni,
                    COUNT(*) as liczba_ofert_razem
                FROM oferty
                WHERE aktywna = 1
                """
            ).fetchone()

            # Profile z JSON-a
            kursor_profile = conn.execute(
                "SELECT profile_json FROM oferty WHERE aktywna = 1"
            ).fetchall()
            wszystkie_profile = set()
            for r in kursor_profile:
                try:
                    for prof in json.loads(r["profile_json"]):
                        wszystkie_profile.add(prof)
                except (json.JSONDecodeError, TypeError):
                    continue

        return {
            "miejscowosci": miejscowosci,
            "wojewodztwa": wojewodztwa,
            "profile": sorted(wszystkie_profile),
            "wyzywienie": wyzywienie,
            "typy_pokoju": typy_pokoju,
            "jednostki_ceny": jednostki_ceny,
            "cena_min": str(zakresy["cena_min"]) if zakresy["cena_min"] is not None else None,
            "cena_max": str(zakresy["cena_max"]) if zakresy["cena_max"] is not None else None,
            "min_dni": zakresy["min_dni"],
            "max_dni": zakresy["max_dni"],
            "liczba_ofert_razem": zakresy["liczba_ofert_razem"],
        }

    def zapisz_przebieg(self, raport: dict) -> int:
        """Zapisuje podsumowanie zaimportowanego przebiegu crawlera."""
        teraz = datetime.now(UTC).isoformat()
        start = raport.get("start", teraz)
        data_przebiegu = start[:10]
        with self.baza.polaczenie() as conn:
            kursor = conn.execute(
                """
                INSERT INTO przebiegi_crawlerow (
                    adapter, data_przebiegu, kompletny, oferty_ok, oferty_odrzucone,
                    bledy_http, raport_json, zaimportowano_o
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    raport.get("adapter", "nieznany"),
                    data_przebiegu,
                    1 if raport.get("kompletny") else 0,
                    raport.get("oferty_ok", 0),
                    raport.get("oferty_odrzucone", 0),
                    raport.get("bledy_http", 0),
                    json.dumps(raport, ensure_ascii=False),
                    teraz,
                ),
            )
            return kursor.lastrowid or 0

    def pobierz_ostatni_przebieg(self) -> dict | None:
        """Zwraca metadane ostatniego zarejestrowanego przebiegu."""
        with self.baza.polaczenie() as conn:
            kursor = conn.execute("SELECT * FROM przebiegi_crawlerow ORDER BY id DESC LIMIT 1")
            wiersz = kursor.fetchone()
            if wiersz is None:
                return None
            return dict(wiersz)

    def policz_aktywne_oferty(self) -> int:
        """Zwraca aktualną liczbę aktywnych ofert w bazie."""
        with self.baza.polaczenie() as conn:
            return conn.execute("SELECT COUNT(*) as c FROM oferty WHERE aktywna = 1").fetchone()[
                "c"
            ]
