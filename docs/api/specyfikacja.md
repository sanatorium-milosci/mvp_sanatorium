# Specyfikacja API Wyszukiwarki Sanatoriów (v1)

Dokument stanowi kontrakt API dla zespołu interfejsu użytkownika (`apps/web/`, Claude Code) oraz zespołu crawlerów (`packages/crawler/`, ChatGPT Work).

## Zasady ogólne

- **Wersja API**: `/api/v1`
- **Format danych**: JSON (kodowanie UTF-8)
- **Format dat**: ISO 8601, np. `2026-09-14` (daty dzienne) lub `2026-09-14T15:30:00Z` (znaczniki czasu UTC)
- **Kwoty i ceny**:
  - Przekazywane jako stringi z dwoma miejscami po przecinku, np. `"1290.00"`, aby uniknąć błędów zaokrągleń zmiennoprzecinkowych.
  - Oznaczenie `cena_od: true` oznacza, że ośrodek podał cenę minimalną ("od 1290 zł").
  - `jednostka`: jedna z wartości:
    - `osobodoba` – cena za jedną osobę za jedną dobę pobytu
    - `turnus_osoba` – cena za cały turnus za jedną osobę
    - `pokoj_doba` – cena za pokój za dobę
- **Szacowany koszt całkowity (`szacowany_koszt_calkowity`)**:
  - Obliczany przez backend **wyłącznie wtedy, gdy dane jednoznacznie na to pozwalają**.
  - Gdy `jednostka == "turnus_osoba"` i podano cenę: koszt całkowity = `cena`.
  - Gdy `jednostka == "osobodoba"`, podano cenę i znana jest liczba dób/dni (`liczba_dni` lub `liczba_nocy`): koszt całkowity = `cena * liczba_dni`.
  - W każdym innym przypadku (np. brak ceny, brak terminu/liczby dni przy cenie za dobę): pole ma wartość `null`.
  - Frontend **nie powinien zgadywać** kosztu, jeśli pole wynosi `null`.
- **Wartości `null`**: Oznaczają „nie ustalono”. Brak wartości nie oznacza „nie ma” ani „fałsz”.

---

## Endpointy

### 1. Lista i wyszukiwanie ofert

`GET /api/v1/oferty`

Przeszukiwanie i filtrowanie ofert z paginacją.

#### Parametry zapytania (Query Params)

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `q` | string | brak | Wyszukiwanie pełnotekstowe w nazwie pakietu, ośrodka i miejscowości |
| `miejscowosc` | string | brak | Filtr po miejscowości (np. `Ustroń`, `Ciechocinek`) |
| `wojewodztwo` | string | brak | Filtr po województwie |
| `profil` | string | brak | Profil leczniczy (wartość z `ProfilLeczniczy`, np. `reumatologiczny`, `kardiologiczny`) |
| `wyzywienie` | string | brak | Standard wyżywienia: `brak`, `sniadania`, `hb`, `fb`, `all_inclusive` |
| `typ_pokoju` | string | brak | Typ pokoju: `jednoosobowy`, `dwuosobowy`, `apartament`, `studio`, `inny` |
| `cena_min` | decimal/string | brak | Minimalna cena podstawowa |
| `cena_max` | decimal/string | brak | Maksymalna cena podstawowa |
| `jednostka_ceny` | string | brak | `osobodoba`, `turnus_osoba`, `pokoj_doba` |
| `min_dni` | int | brak | Minimalna długość pobytu w dniach |
| `max_dni` | int | brak | Maksymalna długość pobytu w dniach |
| `termin_od` | date (YYYY-MM-DD) | brak | Pobyt dostępny od tej daty (termin_od >= data) |
| `termin_do` | date (YYYY-MM-DD) | brak | Pobyt dostępny do tej daty (termin_do <= data) |
| `tylko_dostepne` | bool | `false` | Gdy `true`, zwraca tylko oferty ze statusem `dostepny: true` |
| `basen` | bool | brak | Wymagany basen |
| `winda` | bool | brak | Wymagana winda |
| `parking` | bool | brak | Wymagany parking |
| `zwierzeta` | bool | brak | Możliwość pobytu ze zwierzętami |
| `dostepny_dla_wozka`| bool | brak | Dostępność dla osób na wózkach |
| `sortuj` | string | `najnowsze` | Opcje sortowania: `cena_asc`, `cena_desc`, `dni_asc`, `dni_desc`, `termin_od_asc`, `najnowsze` |
| `pokaz_przeszle` | bool | `false` | Gdy `false` (domyślnie), wyklucza turnusy, których termin_do minął |
| `strona` | int | `1` | Numer strony (od 1) |
| `na_stronie` | int | `20` | Liczba ofert na stronę (1–100) |

#### Odpowiedź (200 OK)

```json
{
  "elementy": [
    {
      "id": 1,
      "adapter": "uzdrowisko_ustron",
      "zrodlo_id": "pakiet-kuracyjny-14",
      "osrodek": {
        "klucz": "uzdrowisko-ustron-rownica",
        "nazwa": "Uzdrowisko Ustroń - Sanatorium Równica",
        "miejscowosc": "Ustroń",
        "wojewodztwo": "śląskie",
        "nip": "5480075548",
        "telefon": "+48 33 854 54 54"
      },
      "pakiet": {
        "nazwa": "Pobyt Kuracyjny z Zabiegami",
        "liczba_dni": 14,
        "liczba_nocy": 13,
        "termin_od": "2026-10-01",
        "termin_do": "2026-10-14",
        "dostepny": true
      },
      "cena": {
        "wartosc": "2980.00",
        "waluta": "PLN",
        "jednostka": "turnus_osoba",
        "cena_od": false,
        "szacowany_koszt_calkowity": "2980.00",
        "doplata_jedynka": "450.00",
        "oplata_klimatyczna_doba": "5.50"
      },
      "standard": {
        "wyzywienie": "fb",
        "typ_pokoju": "dwuosobowy",
        "liczba_zabiegow_dziennie": 3,
        "zabiegi": ["Kąpiel solankowa", "Masaż klasyczny", "Inhalacje"],
        "opieka_lekarska": true
      },
      "profile": ["ortopedyczno_urazowy", "reumatologiczny", "kardiologiczny"],
      "udogodnienia": {
        "winda": true,
        "dostepny_dla_wozka": true,
        "parking": true,
        "parking_platny": false,
        "wifi": true,
        "basen": true,
        "zwierzeta": false,
        "odleglosc_od_centrum_m": 500
      },
      "linki": {
        "url_rezerwacji": "https://uzdrowisko-ustron.pl/rezerwacja/pakiet-14",
        "url_zrodla": "https://uzdrowisko-ustron.pl/pakiety/kuracyjny-14",
        "pobrano_o": "2026-09-14T15:00:00Z"
      }
    }
  ],
  "stronicowanie": {
    "strona": 1,
    "na_stronie": 20,
    "razem": 1,
    "stron_razem": 1
  }
}
```

---

### 2. Szczegóły pojedynczej oferty

`GET /api/v1/oferty/{id}`

Pobiera pełne dane pojedynczej oferty po jej identyfikatorze numerycznym `id`.

#### Odpowiedź (200 OK)
Pojedynczy obiekt w takim samym schemacie jak pojedynczy element z tablicy `elementy` powyżej.

#### Błąd (404 Not Found)
```json
{
  "detail": "Oferta o podanym ID nie została znaleziona"
}
```

---

### 3. Słowniki i opcje filtrów

`GET /api/v1/filtry`

Endpoint pomocniczy dla interfejsu użytkownika, zwracający aktualne warianty filtrów dostępne w bazie danych.

#### Odpowiedź (200 OK)

```json
{
  "miejscowosci": ["Ciechocinek", "Kołobrzeg", "Ustroń"],
  "wojewodztwa": ["kujawsko-pomorskie", "śląskie", "zachodniopomorskie"],
  "profile": [
    "ortopedyczno_urazowy",
    "reumatologiczny",
    "kardiologiczny",
    "naczyn_obwodowych",
    "gorne_drogi_oddechowe",
    "dolne_drogi_oddechowe",
    "uklad_trawienia",
    "endokrynologiczny",
    "cukrzyca",
    "otylosc",
    "osteoporoza",
    "neurologiczny",
    "nerki_drogi_moczowe",
    "skora",
    "kobiecy",
    "psychiczny"
  ],
  "wyzywienie": ["brak", "sniadania", "hb", "fb", "all_inclusive"],
  "typy_pokoju": ["jednoosobowy", "dwuosobowy", "apartament", "studio", "inny"],
  "jednostki_ceny": ["osobodoba", "turnus_osoba", "pokoj_doba"],
  "cena_min": "850.00",
  "cena_max": "4500.00",
  "min_dni": 7,
  "max_dni": 21,
  "liczba_ofert_razem": 12
}
```

---

### 4. Status i zdrowie usługi

`GET /api/v1/zdrowie`

#### Odpowiedź (200 OK)

```json
{
  "status": "ok",
  "wersja_api": "0.1.0",
  "wersja_kontraktu": "0.1.0",
  "baza_ok": true,
  "aktywne_oferty": 12,
  "ostatni_import": "2026-09-14T15:10:00Z"
}
```

---

## Kody błędów HTTP

- `200 OK`: Sukces.
- `400 Bad Request`: Błędne parametry zapytania (np. `termin_do` wcześniejszy niż `termin_od`).
- `404 Not Found`: Nie znaleziono rekordu.
- `422 Unprocessable Entity`: Błąd walidacji formatu parametrów (np. niepoprawny format daty).
- `500 Internal Server Error`: Błąd wewnętrzny serwera.

Wszystkie błędy zwracają JSON z polem `"detail"` lub listą błędów walidacji.
