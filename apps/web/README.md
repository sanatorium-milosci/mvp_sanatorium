# apps/web — interfejs wyszukiwarki pobytów sanatoryjnych

Ścieżka frontendu projektu `mvp_sanatorium` (Claude Code). React + TypeScript + Vite.

## Uruchomienie

```console
cd apps/web
npm install
npm run dev
```

Weryfikacja:

```console
npm run build   # tsc -b && vite build
npm test        # vitest run
npm run lint    # oxlint
```

## Stan obecny

Produkcyjny build domyślnie pobiera **rzeczywiste dane z API tego samego hosta**
(`/api/v1`, przekierowanie przez Caddy). Nie wymaga `VITE_API_BASE_URL`.
Development bez konfiguracji korzysta z danych demonstracyjnych (`src/api/mockData.ts`).
Kształt danych,
typy TS (`src/types/oferta.ts`) i warstwa API (`src/api/`) są już zgodne z realnym
kontraktem backendu opublikowanym przez Antigravity/Michała w
`docs/api/specyfikacja.md` (branch `backend/mvp-api-storage`): zagnieżdżone obiekty
`osrodek`/`pakiet`/`cena`/`standard`/`udogodnienia`/`linki`, `id` liczbowe, paginacja
(`stronicowanie`) i pole `szacowany_koszt_calkowity` liczone przez backend tylko gdy
dane na to jednoznacznie pozwalają. 3 ośrodki, 6 ofert, świadomie z przypadkami
brzegowymi (brak ceny, brak terminu, `cena_od=true`, `dostepny=null`).

Warstwa dostępu do danych jest odizolowana w `src/api/`:

- `src/api/types.ts` — kontrakt `OfertyApi` (`szukaj`, `pobierzSzczegoly`, `pobierzFiltry`)
  oraz typ parametrów `FiltryWyszukiwania` (nazwy 1:1 z query params ze specyfikacji).
- `src/api/mockApi.ts` — implementacja tymczasowa na danych mockowych (filtrowanie,
  sortowanie, paginacja po stronie klienta).
- `src/api/httpApi.ts` — gotowy klient HTTP wg `docs/api/specyfikacja.md`
  (`GET /api/v1/oferty`, `/oferty/{id}`, `/filtry`).
- `src/api/index.ts` — przełącza się automatycznie: jeśli ustawiona jest zmienna
  środowiskowa `VITE_API_BASE_URL` (np. w `apps/web/.env.local`), używany jest
  `httpApi`; bez niej produkcja używa `window.location.origin`, a development
  `mockApi`. Błąd API w produkcji pokazuje stan błędu, bez zastępowania danych
  demonstracyjnymi. Zmienna Vite jest odczytywana podczas budowania aplikacji.

## Struktura

```text
src/types/oferta.ts        lustrzane typy TS dla kontraktu Oferta (packages/core/models.py)
src/api/                   warstwa danych (patrz wyżej)
src/components/            komponenty UI wielokrotnego użytku
src/pages/                 widoki: wyszukiwarka (SearchPage), szczegóły (OfferDetailsPage)
src/utils/format.ts        formatowanie cen, dat, terminów po polsku
```

## Funkcje

- Wyszukiwanie pełnotekstowe + filtry: miejscowość, profil leczniczy, wyżywienie,
  cena maksymalna, termin od, tylko dostępne.
- Lista ofert z ceną (z jednostką i oznaczeniem „od”), terminem, dostępnością i datą
  pobrania danych.
- Szczegóły oferty: zabiegi, udogodnienia, kontakt, link do ośrodka i rezerwacji.
- Stany: ładowanie, brak wyników, błąd (z możliwością ponowienia).
- Układ mobile-first, w pełni po polsku.
- `None`/`null` z kontraktu zawsze renderowane jako „nie ustalono” — bez zgadywania.

Testy wymagają Node zgodnego z lockfile (np. Node 24.19.0; Node 22.15.0 jest
za stary dla obecnego jsdom). CI sprawdza testy, build i lint na Node 24.
