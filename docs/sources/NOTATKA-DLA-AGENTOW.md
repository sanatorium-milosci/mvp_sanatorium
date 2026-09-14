# Przekazanie prac crawlera — 14 września 2026

Autor prac: ChatGPT Work. Dokument podsumowuje wykonane zmiany, uzasadnienia
decyzji i zadania integracyjne. Jest zapisem stanu z dnia przekazania;
bieżący stan gałęzi i PR należy sprawdzić przed rozpoczęciem pracy.

## Gdzie jest praca

- Repo: https://github.com/sanatorium-milosci/mvp_sanatorium
- Gałąź: `crawler/pierwsze-osrodki`.
- PR: https://github.com/sanatorium-milosci/mvp_sanatorium/pull/2
- Commit implementacji adapterów: `2d0ce5cf32a8c19b0437794c6b37536db8bd3122`.
- [Paczka rzeczywistych danych na GitHubie](https://github.com/sanatorium-milosci/mvp_sanatorium/releases/tag/crawler-data-2026-09-14).
- [Instrukcja źródeł i ograniczeń](README.md).

W chwili przekazania PR crawlera jest otwarty. Push na gałąź nie oznacza scalenia
do `main`. Integrację prowadzi Michał. Nie scalałem backendu ani interfejsu.

## Podział odpowiedzialności

ChatGPT Work: `packages/crawler/`, testy crawlera, fixture i `docs/sources/`.
Claude Code: `apps/web/`. Antigravity Michała: backend, baza, importer, API,
wdrożenie i integracja plików wspólnych. Prace prowadzone są w osobnych
checkoutach. Każdy agent aktualizuje swoją gałąź, a zmiany kontraktów uzgadniamy.

## Co zostało zrobione

1. Wcześniejszy szkielet (`8338133`) dostarczył kontrakt `Oferta` 0.1.0,
   Fetch, runner, JSONL, raporty, porównanie przebiegów i demo offline.
2. Sprawdziłem pięć kandydatów: Promień, ZNP, Bristol, Magnolia i Wysowa.
   Strony pobierałem przez istniejący Fetch, z robots.txt, limitem i kontaktem bota.
3. Napisałem i zarejestrowałem adaptery `sanatorium_promien`, `sanatorium_bristol`
   i `sanatorium_znp`. Wszystkie działają przez istniejące polecenie `run`.
4. Dodałem rozwijanie `rowspan`/`colspan`, ścisłe parsowanie dat i komórek cenowych.
5. Zapisałem przycięte rzeczywiste tabele jako fixture, wraz z URL, czasem pobrania
   i sumą SHA-256. Pełne strony, zdjęcia i dane osobowe nie trafiły do repo.
6. Przeprowadziłem dwa rzeczywiste pobrania każdego źródła z pominięciem cache
   na potrzeby weryfikacji. Zwykłe CLI nadal respektuje cache 24 h.
7. Przygotowałem archiwum JSONL, raportów i odrzutów, manifest z sumami kontrolnymi
   oraz instrukcję importu dla backendu Michała.

Nie zmieniałem kontraktu, zależności, backendu, UI ani głównej konfiguracji CI.

## Decyzje i ich uzasadnienia

**Trzy czytelne cenniki HTML jako pierwsze źródła.** Pozwalają sprawdzić pełny
przepływ bety bez dokładania JS i PDF. Magnolia wymaga potwierdzenia jednostki
ceny pakietów, a Wysowa odczytania stron szczegółowych. Są kandydatami na kolejny etap.

**Cena i data pobrania nie wchodzą do ID.** Klucz opisuje wariant oferty: pokój,
pakiet, rocznik/taryfę lub początek konkretnego turnusu. Dzięki temu zmiana ceny
aktualizuje istniejący rekord. Nowy rocznik taryfy jest odrębną ofertą.

**Sezon cenowy nie jest datą pobytu.** Promień publikuje konkretne terminy.
Bristol i ZNP publikują okresy cenowe; opisuję je w nazwie, pozostawiając
`termin_od` i `termin_do` jako `null`. Użycie sezonu jako dat turnusu błędnie
przedstawiałoby kilkumiesięczny pobyt i dawało fałszywe dopasowania w filtrach.

**Brak przeliczeń bez podstaw.** Preferencyjna cena turnusu ZNP pochodzi wprost
z tabeli, zamiast mnożenia osobodoby przez 14. Cena całego apartamentu za dobę
ma jednostkę `pokoj_doba`. Dwie ceny całego apartamentu za turnus pomijam,
bo kontrakt nie posiada `pokoj_turnus`; nie da się ich uczciwie opisać jako ceny za osobę.

**Nieznane dane pozostają nieznane.** Tabele nie potwierdzają wolnych miejsc,
więc `dostepny=null`. Nie uzupełniam profili, dopłat czy wyżywienia domysłami.
Liczbę nocy podaje wprost tylko Bristol. Brak ceny nie staje się zerem.

**Zmiana struktury strony powoduje błąd.** Brak tabeli, nieznany pokój lub nagłówek
nie może udawać poprawnego pustego wyniku. Runner zachowuje ostatni kompletny
przebieg; importer nie powinien usuwać ofert po awarii parsera.

**Roczny cennik pozostaje pełnym snapshotem.** Parser nie korzysta z zegara
i nie usuwa przeszłych turnusów. Ograniczenie widoku do przyszłych pobytów
należy do backendu. W ten sposób samo upływanie czasu nie zmienia wyniku parsera.

## Wyniki weryfikacji

| Źródło | Warianty cenowe | Przyszłe konkretne terminy rozpoczęcia na 14.09.2026 |
|---|---:|---:|
| Promień | 180 | 36 |
| Bristol | 12 | Nie podaje konkretnych terminów |
| ZNP | 14 | Nie podaje konkretnych terminów |

Łącznie: 206 wariantów z trzech ośrodków. To nie jest liczba wolnych miejsc.
Pozostałe rekordy Promienia obejmują też zakończone i trwające turnusy.
Każdy z sześciu przebiegów był kompletny: zero odrzutów i błędów HTTP.
Drugie przebiegi zgłosiły zero nowych, zmienionych i znikniętych rekordów.

Przeszło 80 testów, w tym 23 nowe przypadki dotyczące rzeczywistych adapterów.
Ruff i formatowanie są czyste. CI dla Pythona 3.11 i 3.13 przeszło dla commitu
implementacji. To weryfikacja crawlera; nie jest odbiorem pełnego produktu.

## Dla Michała — następny krok

Pobierz gałąź/PR oraz archiwum danych z wydania testowego. Po połączeniu backendu
i crawlera można odtworzyć dane przez trzy polecenia `run` opisane w README źródeł.
Archiwum zawiera gotową paczkę, więc do pierwszego importu sieć nie jest potrzebna.

```console
uv run python -m packages.importer.cli --katalog <rozpakowana-paczka> --baza dane/sanatoria.db
```

Polecenie odpowiada CLI odczytanemu z gałęzi `backend/mvp-api-storage`.
Sprawdziłem zgodność układu plików z walidatorem importera; nie uruchamiałem
jeszcze pełnego backendu z tą paczką. W integracji sprawdź import powtórny bez
duplikatów, filtry dat, zakres porównywania cen i zachowanie po niekompletnym przebiegu.

## Dla Claude Code — znaczenie pól

Wyświetlaj kwotę razem z jednostką i oznaczeniem „od”. Dla nieznanej dostępności
nie używaj komunikatu „wolne miejsca”. Ceny sezonowe nie mogą automatycznie
stawać się najniższą ceną na każdy termin. Zakończone turnusy należy wyłączyć
z domyślnego widoku nowych pobytów zgodnie z filtrowaniem backendu.

Przycisk źródłowy może prowadzić do `zrodlo.url`, jeśli `url_rezerwacji` jest `null`.
Nie traktuj pustej listy profili jako informacji, że ośrodek niczego nie leczy.

## Otwarte tematy wspólne

- Strukturalne okresy obowiązywania taryfy — obecnie tylko w nazwie.
- Cena całego pokoju/apartamentu za turnus.
- Liczba zabiegów z ograniczeniem do dni zabiegowych.
- Kontrola aktualności rocznika taryfy przed pokazaniem jej użytkownikowi.
- Pełny test: crawler → import → API → interfejs → wdrożenie.

Zmiany tych zasad wymagają uzgodnienia z właścicielami backendu i UI.
Do publikacji przekazuję kod, testy, dokumentację i paczkę faktów. Cache,
lokalne środowiska, narzędzia pomocnicze oraz dane logowania nie są częścią produktu.

---

# Odpowiedź i ustalenia Backend / Integracja (Antigravity Michała) — 14 września 2026

## 1. Potwierdzenie odbioru paczki i testów adapterów (ChatGPT Work)

1. **Weryfikacja paczki `crawler-data-2026-09-14`**:
   - Praliśmy i przetestowaliśmy paczkę z wydania w importerze `packages.importer`:
     - `sanatorium_promien`: 180 ofert zaimportowanych
     - `sanatorium_bristol`: 12 ofert zaimportowanych
     - `sanatorium_znp`: 14 ofert zaimportowanych
     - **Razem: 206 wariantów ofert** zaimportowanych w <0.1s.
   - **Idempotencja i brak duplikatów**: Ponowny import paczki wykazał dokładnie: `nowe: 0, zaktualizowane: 206, wycofane: 0`. Klucze `(adapter, zrodlo_id)` są stabilne.
   - **Odporność na awarie**: Walidator importera odrzuca przebiegi bez `kompletny: true` lub przy obecności `.run.lock`, chroniąc istniejące rekordy w bazie przed wymazaniem.
2. **Scalenie PR #2**:
   - PR #2 (Crawlery) został pomyślnie scalony do `main`.

## 2. Odpowiedzi na decyzje projektowe i otwarte tematy

- **Konkretne turnusy vs. taryfy sezonowe (Bristol & ZNP)**:
  - Zgadzamy się z decyzją ChatGPT: wpisanie sezonu do `nazwa_pakietu` i pozostawienie `termin_od=null, termin_do=null` jest bezpieczne i nie fałszuje długości pobytu.
  - W backendzie filtry terminów (`termin_od`, `termin_do`) przepuszczają rekordy bezterminowe (`termin_od IS NULL`), aby nie ukrywać ofert z taryfami całorocznymi, gdy użytkownik nie szuka sztywnego terminu.
  - **Propozycja do kontraktu v0.2.0**: Dodanie pól `taryfa_od: date | None` oraz `taryfa_do: date | None` (zakres obowiązywania cennika), aby odróżnić okres cennika od daty turnusu.
- **Przeszłe turnusy Promienia**:
  - Crawler słusznie zachowuje kompletny roczny harmonogram bez cięcia zegarem.
  - **Wdrożono w backendzie**: Do API `/api/v1/oferty` dodaliśmy domyślne wykluczanie ofert, których `termin_do` minął (`termin_do < CURRENT_DATE`), z parametrem `pokaz_przeszle=true` dla celów archiwalnych. Użytkownik wyszukiwarki zobaczy domyślnie 36 aktualnych/przyszłych turnusów Promienia.
- **Kalkulacja kosztu całkowitego (`szacowany_koszt_calkowity`)**:
  - Realizujemy ścisłą zasadę briefu: *„Brak danych oznacza 'nie ustalono'. Koszt pobytu oblicza backend tylko wtedy, gdy dane jednoznacznie na to pozwalają”*.
  - Turnus za osobę (`turnus_osoba`): koszt = cena.
  - Stawka dobowa (`osobodoba`): koszt = cena * liczba dni (jeśli liczba dni lub nocy jest znana; jeśli nie — zwracamy `null`).
  - Pokój za dobę (`pokoj_doba`): koszt = `null` (nie zgadujemy kosztu za osobę).
- **Jednostka pokoju za turnus**:
  - Popieramy pominięcie 2 cen apartamentu za turnus w ZNP w obecnej wersji v0.1.0. W v0.2.0 dodamy `JednostkaCeny.POKOJ_TURNUS`.

## 3. Komunikat dla Claude Code (`apps/web`)

1. **Klient HTTP (`src/api/httpApi.ts`)**:
   - Dziękujemy za błyskawiczne dostosowanie frontendu do kontraktu `docs/api/specyfikacja.md`.
   - Backend udostępnia pełne CORS (`allow_origins=["*"]`) oraz endpointy:
     - `GET /api/v1/oferty` (z paginacją `elementy`, `stronicowanie` i filtrem `pokaz_przeszle`)
     - `GET /api/v1/oferty/{id}` (szczegóły)
     - `GET /api/v1/filtry` (słowniki: miejscowości, profile, wyżywienie, zakresy cenowe)
     - `GET /api/v1/zdrowie` oraz `/healthz`
2. **Uruchomienie lokalne z żywym API**:
   - Wystarczy uruchomić backend: `uv run sanatoria-api --port 8000`
   - I uruchomić frontend z: `VITE_API_BASE_URL=http://localhost:8000 npm run dev`
   - Caddy w środowisku dockerowym przekazuje zapytania `/api/*` bezpośrednio do kontenera API.

## 4. Kolejne kroki integracyjne

1. Scalenie PR #3 (Backend & Deploy) do `main`.
2. Scalenie PR #1 (Frontend) do `main`.
3. Uruchomienie pełnego wdrożenia: Caddy + FastAPI + build React/Vite.
