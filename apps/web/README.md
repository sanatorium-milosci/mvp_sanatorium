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

Interfejs działa **na danych mockowych** (`src/api/mockData.ts`) zgodnych z kontraktem
`Oferta` z `packages/core/models.py` (wersja `0.1.0`): 3 ośrodki, 6 ofert, świadomie
zawierające przypadki brzegowe (brak ceny, brak terminu, `cena_od=true`, `dostepny=null`).

Warstwa dostępu do danych jest odizolowana w `src/api/`:

- `src/api/types.ts` — kontrakt `OfertyApi` (metody `szukaj` i `pobierzSzczegoly`) oraz
  typ filtrów `FiltryWyszukiwania`.
- `src/api/mockApi.ts` — implementacja tymczasowa na danych mockowych.
- `src/api/index.ts` — **jedyne miejsce**, w którym trzeba podmienić `mockOfertyApi` na
  prawdziwego klienta HTTP, gdy backend (Antigravity/Michał) opublikuje kontrakt w
  `docs/api/`. Reszta aplikacji importuje wyłącznie `ofertyApi` z `src/api`, więc podmiana
  nie wymaga zmian w komponentach.

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

## Do zrobienia po publikacji `docs/api/`

1. Podmienić `mockOfertyApi` w `src/api/index.ts` na klienta HTTP wg opublikowanego kontraktu.
2. Usunąć/zredukować `src/api/mockData.ts` (lub zostawić do testów/Storybooka).
3. Dostosować `FiltryWyszukiwania`, jeśli realne API różni się od założeń.
