-- Schemat bazy danych SQLite dla wyszukiwarki ofert sanatoryjnych

CREATE TABLE IF NOT EXISTS oferty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adapter TEXT NOT NULL,
    zrodlo_id TEXT NOT NULL,
    osrodek_klucz TEXT NOT NULL,
    osrodek_nazwa TEXT NOT NULL,
    miejscowosc TEXT NOT NULL,
    wojewodztwo TEXT,
    nip TEXT,
    nazwa_pakietu TEXT NOT NULL,
    liczba_dni INTEGER,
    liczba_nocy INTEGER,
    termin_od TEXT,
    termin_do TEXT,
    dostepny INTEGER,
    cena TEXT,
    jednostka_ceny TEXT,
    waluta TEXT NOT NULL DEFAULT 'PLN',
    cena_od INTEGER NOT NULL DEFAULT 0,
    wyzywienie TEXT,
    typ_pokoju TEXT,
    doplata_jedynka TEXT,
    liczba_zabiegow_dziennie INTEGER,
    zabiegi_json TEXT NOT NULL DEFAULT '[]',
    opieka_lekarska INTEGER,
    oplata_klimatyczna_doba TEXT,
    profile_json TEXT NOT NULL DEFAULT '[]',
    udogodnienia_json TEXT NOT NULL DEFAULT '{}',
    telefon TEXT,
    url_rezerwacji TEXT,
    zrodlo_url TEXT NOT NULL,
    pobrano_o TEXT NOT NULL,
    wersja_adaptera TEXT NOT NULL,
    hash_tresci TEXT NOT NULL,
    aktywna INTEGER NOT NULL DEFAULT 1,
    utworzono_o TEXT NOT NULL,
    zaktualizowano_o TEXT NOT NULL,
    CONSTRAINT uq_oferta_adapter_zrodlo UNIQUE (adapter, zrodlo_id)
);

CREATE INDEX IF NOT EXISTS idx_oferty_adapter_zrodlo ON oferty (adapter, zrodlo_id);
CREATE INDEX IF NOT EXISTS idx_oferty_miejscowosc ON oferty (miejscowosc);
CREATE INDEX IF NOT EXISTS idx_oferty_wojewodztwo ON oferty (wojewodztwo);
CREATE INDEX IF NOT EXISTS idx_oferty_termin ON oferty (termin_od, termin_do);
CREATE INDEX IF NOT EXISTS idx_oferty_aktywna ON oferty (aktywna);
CREATE INDEX IF NOT EXISTS idx_oferty_cena ON oferty (CAST(cena AS NUMERIC));

CREATE TABLE IF NOT EXISTS przebiegi_crawlerow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adapter TEXT NOT NULL,
    data_przebiegu TEXT NOT NULL,
    kompletny INTEGER NOT NULL,
    oferty_ok INTEGER NOT NULL,
    oferty_odrzucone INTEGER NOT NULL DEFAULT 0,
    bledy_http INTEGER NOT NULL DEFAULT 0,
    raport_json TEXT NOT NULL,
    zaimportowano_o TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_przebiegi_adapter_data ON przebiegi_crawlerow (adapter, data_przebiegu);
