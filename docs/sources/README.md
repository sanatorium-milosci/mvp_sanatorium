# Pierwsze rzeczywiste źródła — przekazanie do integracji

Trzy adaptery korzystają z istniejącego `Fetch`, runnera i kontraktu `Oferta` 0.1.0.
Nie dodają zależności ani nie zmieniają bazy, API, interfejsu lub modeli wspólnych.

| Adapter | Źródło | Zakres |
|---|---|---|
| `sanatorium_promien` | [Promień, Ciechocinek](https://www.sanatoriumpromien.pl/cennik-pobytow-pelnoplatnych) | 7- i 14-dniowe turnusy, daty przyjazdu/wyjazdu i cztery warianty pokoju |
| `sanatorium_bristol` | [Bristol, Kudowa-Zdrój](https://sankud.pl/cennik-sanatoryjny/) | 8 dni / 7 nocy, cztery warianty pokoju i trzy taryfy sezonowe |
| `sanatorium_znp` | [ZNP, Ciechocinek](https://znpciechocinek.pl/cennik/cennik-indywidualni/) | Osobodoby, turnusy 14 dni za osobę i doba całego apartamentu |

## Uruchomienie dla Michała

Po pobraniu gałęzi / scaleniu PR:

```console
uv sync --locked
uv run sanatoria-crawler list
uv run sanatoria-crawler run sanatorium_promien
uv run sanatoria-crawler run sanatorium_bristol
uv run sanatoria-crawler run sanatorium_znp
```

Ustaw wcześniej zmienną `SANATORIA_USER_AGENT` ze stroną informacyjną bota
i rzeczywistym kontaktem. CLI nie wczytuje automatycznie pliku `.env`.
Argument `--out <katalog>` pozwala zapisać paczki w katalogu importera.
`--cache <katalog>` wskazuje trwały cache. Należy zachować limit 1 żądania/s/domenę.
Zwykły przebieg ma cache 24 h; ponowne uruchomienie z cache zachowuje oryginalny czas pobrania.

Każdy adapter zapisuje standardowe JSONL, odrzuty i raport.
Importer odczytuje wyłącznie kompletny raport (`kompletny=true`) i czeka na brak
`.run.lock`. Zniknięcia rozpatruje wyłącznie w obrębie tego adaptera.
Identyfikator importu oferty: `(adapter, zrodlo_id)`. Ośrodek: `(adapter, osrodek_klucz)`.

## Znaczenie danych — ważne dla backendu i interfejsu

- Rekord oznacza wariant cennika: pakiet, pokój, taryfę lub termin. Nie oznacza
  osobnego ośrodka ani potwierdzonej dostępności. `dostepny` pozostaje `null`.
- Promień podaje konkretne terminy: trafiają do `termin_od` i `termin_do`.
  Roczny cennik zawiera też turnusy zakończone. Backend powinien domyślnie
  odfiltrować zakończone terminy w widoku nowych pobytów, zachowując je w historii.
- Bristol i ZNP podają okresy obowiązywania taryf, a nie konkretne terminy pobytu.
  Te okresy zapisujemy czytelnie w `nazwa_pakietu`; `termin_od` i `termin_do`
  pozostają `null`. Nie wolno traktować ich jako potwierdzonego dopasowania
  do wskazanych dat, ani automatycznie stosować najtańszej taryfy przez cały rok.
- Ceny pakietów Bristol i osobowych turnusów ZNP/Promień dotyczą całego pakietu
  za osobę. W ZNP cena pakietu 14 dni jest osobną ceną z tabeli, a nie 14-krotnością stawki dobowej.
- Doba całego apartamentu ZNP ma `jednostka_ceny=pokoj_doba`. Nie porównujemy
  jej z osobodobą. **Dwie ceny całego apartamentu za turnus są celowo pominięte**:
  kontrakt nie ma jednostki `pokoj_turnus`. Nie przeliczamy ich na cenę za osobę.
- Pokój trzyosobowy i dostawka mają `typ_pokoju=inny`; szczegół pozostaje w nazwie.
- Brak ceny daje `cena=null`, a nie zero. Jawne „od” daje `cena_od=true`.
- Nie ustalamy liczby nocy na podstawie liczby dni. Jedynie Bristol podaje obie liczby.
- Nie dopisujemy profili leczniczych, liczby posiłków, zabiegów ani dodatkowych opłat,
  których nie odczytujemy z tych tabel. Cena źródłowa nie jest gwarancją kosztu
  wraz ze wszystkimi opłatami lokalnymi i opcjonalnymi usługami.
- `url_rezerwacji` pozostaje `null`; przycisk „Sprawdź ofertę” może prowadzić do `zrodlo.url`.

Do wspólnego uzgodnienia później: strukturalne okresy obowiązywania taryfy,
jednostka ceny całego pokoju za turnus i rozkład zabiegów w dni robocze.
Obecny PR nie zmienia kontraktu.

## Stabilność i awarie

Klucze nie zawierają ceny, kolejności wiersza ani daty pobrania. Rozróżniają
pokoje, długości pakietów, taryfy roczne oraz datę rozpoczęcia konkretnego turnusu.
Zmiana ceny zachowuje ID. Nowy rocznik cennika sezonowego jest nową ofertą taryfową.

Parsery weryfikują nagłówki i strukturę tabel, rozwijają `rowspan`/`colspan`
i odrzucają nieznane pokoje oraz jednostki. Zmiana HTML kończy się odrzutem strony
i niekompletnym raportem; nie powinna powodować masowego wycofania ofert.
Brak jednego z dwóch cenników Promienia również jest błędem.

`hash_tresci` jest SHA-256 rzeczywistej tabeli będącej podstawą oferty.
Nie pobieramy stron poza domenami adaptera, nie logujemy się i nie obchodzimy blokad.

## Fixture i testy

`tests/fixtures/crawler/{promien,bristol,znp}/cennik.html` zawierają wyłącznie
rzeczywiste tabele cenowe, bez zdjęć, marketingu, opinii, danych osobowych i skryptów.
Usunięto atrybuty prezentacyjne; zachowano strukturę komórek i tekst cen.
`source.json` podaje URL, datę pobrania i SHA-256 fixture.

Testy obejmują konkretne ceny i daty, brak ceny, cenę „od”, stabilność ID po zmianie
ceny, utratę tabeli, rozróżnienie sezonu od turnusu oraz pełny przebieg i powtórny importowy JSONL.

```console
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Źródła rezerwowe

- [Magnolia, Ustroń](https://hotel-magnolia.pl/cennik-2026): HTML dostępny;
  przed adapterem trzeba jednoznacznie potwierdzić jednostkę ceny pakietów.
- [Uzdrowisko Wysowa](https://www.uzdrowisko-wysowa.pl/pobyt.html): lista pobytów
  dostępna; adapter wymaga przejścia do szczegółów poszczególnych pakietów.

Surowy HTML jest wyłącznie lokalnym cache. Wyników `out/`, cache i paczek
produkcyjnych nie commitujemy do repozytorium. Archiwum danych dla integracji
zawiera jedynie JSONL, odrzuty, raporty oraz manifest z sumami SHA-256.
