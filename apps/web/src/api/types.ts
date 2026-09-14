import type {
  JednostkaCeny,
  ListaOfert,
  Oferta,
  ProfilLeczniczy,
  SlownikiFiltrow,
  TypPokoju,
  Wyzywienie,
} from '../types/oferta'

export type Sortowanie = 'cena_asc' | 'cena_desc' | 'dni_asc' | 'dni_desc' | 'termin_od_asc' | 'najnowsze'

/** Parametry zapytania GET /api/v1/oferty — nazwy 1:1 z docs/api/specyfikacja.md. */
export interface FiltryWyszukiwania {
  q?: string
  miejscowosc?: string
  wojewodztwo?: string
  profil?: ProfilLeczniczy
  wyzywienie?: Wyzywienie
  typ_pokoju?: TypPokoju
  cena_min?: number
  cena_max?: number
  jednostka_ceny?: JednostkaCeny
  min_dni?: number
  max_dni?: number
  termin_od?: string // ISO date
  termin_do?: string // ISO date
  tylko_dostepne?: boolean
  basen?: boolean
  winda?: boolean
  parking?: boolean
  zwierzeta?: boolean
  dostepny_dla_wozka?: boolean
  sortuj?: Sortowanie
  strona?: number
  na_stronie?: number
}

/** Błąd zwracany przez warstwę API — odróżniany od braku wyników. */
export class BladApi extends Error {}

/**
 * Kontrakt, wg którego pracuje interfejs — zgodny z docs/api/specyfikacja.md.
 * Implementacja mockowa (mockApi.ts) będzie zastąpiona klientem HTTP (httpApi.ts)
 * po wdrożeniu backendu; patrz src/api/index.ts.
 */
export interface OfertyApi {
  szukaj(filtry: FiltryWyszukiwania): Promise<ListaOfert>
  pobierzSzczegoly(id: string): Promise<Oferta | null>
  pobierzFiltry(): Promise<SlownikiFiltrow>
}
