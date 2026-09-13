# Crawler ofert sanatoryjnych

Szkielet ścieżki B projektu `sanatorium-milosci/mvp_sanatorium`: zbieranie faktów
o pełnopłatnych pobytach i przekazywanie ich ścieżce A jako JSONL.
Python 3.11+, zarządzanie zależnościami przez [uv](https://docs.astral.sh/uv/).

## Co działa

- Kontrakt `Oferta` w Pydantic v2, wersja `0.1.0`, odtworzony z briefu v1.0.
- Asynchroniczny HTTPX, maksymalnie jedno żądanie na sekundę na domenę,
  współbieżność, robots.txt, cache dyskowy 24 h, do trzech prób przy 429/5xx
  i błędach transportu. Dłuższy `Crawl-delay` / `Request-rate` jest respektowany.
- Jawna lista domen i weryfikacja każdego przekierowania; brak logowania
  i obchodzenia blokad. 401/403, 429 i zakazy robots trafiają do raportu.
- Rejestr adapterów, czyste parsery, walidacja przed zapisem, odrzuty, raporty,
  porównanie ceny, terminu i dostępności po `(adapter, zrodlo_id)`.
- Powtarzalne demo offline, testy i GitHub Actions. Demo używa wyłącznie
  fikcyjnej fixture i transportu HTTP w pamięci; nie kontaktuje się z ośrodkami.

**Nie ma jeszcze adapterów produkcyjnych.** Lista pięciu ośrodków M1 oraz
prawdziwy URL strony bota i kontakt czekają na ustalenie. PDF i Playwright
są kolejnymi etapami; `wymaga_js=True` kończy się jawnym komunikatem.
Baza, integracje rejestrów, API, frontend i harmonogram nie wchodzą w ten szkielet.

## Uruchomienie

```console
uv sync --locked
uv run sanatoria-crawler list
uv run sanatoria-crawler demo
uv run sanatoria-crawler demo
```

Pierwszy przebieg tworzy dwie oferty; drugi zgłasza zero zmian. Dni, ceny
i nazwy z demo są syntetyczne i nie nadają się do importu produkcyjnego.
Alternatywny punkt wejścia: `uv run python -m packages.crawler demo`.

Weryfikacja:

```console
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Po dodaniu adaptera produkcyjnego:

```console
uv run sanatoria-crawler run nazwa_adaptera --user-agent "SanatoriaBot/1.0 (+https://domena.pl/bot; kontakt@domena.pl)"
```

Podmień adresy na własne, działające dane kontaktowe. Można ustawić
`SANATORIA_USER_AGENT` zamiast flagi. `.env.example` dokumentuje ustawienie,
ale CLI celowo nie wczytuje automatycznie pliku `.env`. Opcje `--out`,
`--cache` i `--wspolbieznosc` pozwalają zmienić katalogi i limit równoległości.
Limit 1 żądania/s obejmuje także robots.txt i kolejne próby.

## Pliki wyjściowe

```text
out/<adapter>/<YYYY-MM-DD>.jsonl
out/<adapter>/<YYYY-MM-DD>.odrzuty.jsonl
out/<adapter>/<YYYY-MM-DD>.raport.json
out/<adapter>/.ostatni-kompletny.jsonl
```

Daty i znaczniki czasu są w UTC. Każda linia głównego JSONL to zwalidowana
`Oferta`; kwoty Decimal są zapisane jako napisy JSON, bez utraty precyzji.
`None` oznacza brak ustalenia. Ceny „od” mają `cena_od=true`.
Odrzuty zawierają URL, etap i pole `blad`; nie przechowują pełnego HTML
ani wartości wejściowych błędów Pydantic. Gdy parser nie zdoła utworzyć
rekordów strony, raport liczy jeden odrzut strony.

Raport zawiera pola z briefu, a także `kompletny`, `bledy`, `trafienia_cache`
i `do_kontaktu`. **Przy niekompletnym przebiegu `zmiany` jest `null`**:
nie wyciągamy wniosków o zniknięciu ofert z awarii sieci lub parsera.
Ścieżka A powinna importować wyłącznie raporty z `kompletny=true` i po
zwolnieniu `.run.lock`. Pusty wynik po niepustym kompletnym przebiegu
również wymaga sprawdzenia adaptera, zamiast zgłaszać masowe zniknięcia.

Kolejny przebieg tego samego dnia zastępuje dzienne pliki. Porównanie jest
zawsze względem ostatniego **kompletnego** przebiegu, także z tego samego dnia.
Plik `.ostatni-kompletny.jsonl` zachowuje tę bazę po błędzie. To nie jest jeszcze
pełna historia snapshotów z M3. Nie usuwaj bazy, jeśli chcesz zachować ciągłość.

Blokada `.run.lock` zapobiega równoczesnym zapisom jednego adaptera. Po awarii
procesu sprawdź, czy nie działa już żaden przebieg, i dopiero wtedy usuń osieroconą
blokadę. Uszkodzona baza poprzedniego przebiegu zatrzymuje pracę zamiast
potraktować wszystkie oferty jako nowe. Zapisy pojedynczych plików są atomowe;
nie jest to transakcja obejmująca cały katalog.

`out/`, `.cache/`, `.env` i bazy danych są ignorowane przez Git.
Cache przechowuje lokalny HTML na potrzeby parsera, nie jest eksportowany.
Nie umieszczaj w publicznym repo pełnych stron, zdjęć, opisów ani danych osobowych.

## Dodanie adaptera

1. Utwórz `packages/crawler/adaptery/<nazwa>.py` z interfejsem `Adapter`.
2. W `zbierz_urle(fetch)` pobieraj strony i paginację przez `await fetch.get(url)`.
   Wynik `Strona` zawiera `html`, końcowy `url` i rzeczywisty `pobrano_o`.
   Błąd odkrywania ofert musi być zgłoszony, nie zamieniany w pustą listę.
3. W `parsuj(html, url)` zwracaj `list[Oferta]`, bez sieci, plików i zegara.
   `zrodlo_fragmentu` liczy SHA-256 fragmentu i podstawia stały czas techniczny;
   runner przed zapisem zastępuje go czasem pobrania (zachowanym również w cache).
   Brak oczekiwanej struktury strony powinien powodować błąd parsera.
4. Użyj stabilnego ID ze strony lub sluga URL; warianty pakietu wymagają osobnych
   stabilnych kluczy. Cena i data pobrania nie mogą stanowić części klucza.
5. Dodaj przycięte fixture faktów w `tests/fixtures/crawler/<nazwa>/` i co najmniej
   dwa testy w `tests/crawler/`: konkretne wartości oraz przypadek brzegowy.
   Fixture produkcyjne powinny pochodzić z realnej strony i mieć opis źródła.
6. Zarejestruj adapter w `rejestr_produkcyjny()`, uruchom kontrole i prześlij PR.

Zbieramy tylko fakty: ceny, daty, zabiegi, wyposażenie i kontakt firmowy.
Nie zbieramy opisów marketingowych, zdjęć, opinii ani kontaktów pracowników.
`parsuj_cene` przyjmuje np. `1 290,00 zł`; nie zgaduje kwoty z zakresu czy prozy.

## Układ i własność

```text
packages/core/models.py      kontrakt 0.1.0 — strefa wspólna / Jan
packages/crawler/baza.py     protokół, rejestr, pomocnicze parsowanie
packages/crawler/fetch.py    HTTP, robots, cache, retry, limity
packages/crawler/runner.py   walidacja, zapis, raport i stan przebiegów
packages/crawler/zmiany.py   porównanie ofert
packages/crawler/adaptery/   adaptery domenowe (obecnie tylko demo offline)
tests/crawler/              testy bez dostępu do sieci
tests/fixtures/crawler/     przypadki HTML
```

To inicjalizacja pustego repo wskazanego przez użytkownika, a nie repo
`sanatoria-data` wymienionego jako planowane w briefie. Model został utworzony
z podanego kontraktu, bez zmiany pól i wersji. Kolejne zmiany `packages/core/`
wymagają uzgodnienia obu ścieżek, PR i wersjonowania kontraktu. Crawler nie
tworzy ani nie modyfikuje `packages/registry/` i nie potrzebuje dostępu do bazy.
Nowe prace prowadź na gałęziach `crawler/...`; przed pushem wykonaj
`git pull --rebase origin main`. Pierwszy commit pustego repo inicjuje `main`.

Dokumentacja zależności: [HTTPX](https://www.python-httpx.org/async/),
[Pydantic](https://docs.pydantic.dev/latest/concepts/models/),
[uv — lock i sync](https://docs.astral.sh/uv/concepts/projects/sync/).
