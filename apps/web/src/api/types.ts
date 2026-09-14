import type { JednostkaCeny, Oferta, ProfilLeczniczy, Wyzywienie } from '../types/oferta'

export interface FiltryWyszukiwania {
  fraza?: string // wyszukiwanie po nazwie ośrodka, miejscowości lub pakietu
  miejscowosc?: string
  profil?: ProfilLeczniczy
  wyzywienie?: Wyzywienie
  jednostkaCeny?: JednostkaCeny
  cenaMax?: number
  terminOd?: string // ISO date — pobyt musi zaczynać się nie wcześniej
  terminDo?: string // ISO date — pobyt musi kończyć się nie później
  tylkoDostepne?: boolean
}

export interface WynikWyszukiwania {
  oferty: Oferta[]
  liczbaWszystkich: number
}

/** Błąd zwracany przez warstwę API — odróżniany od braku wyników. */
export class BladApi extends Error {}

/**
 * Kontrakt, wg którego pracuje interfejs. Implementacja mockowa (mockApi.ts)
 * będzie zastąpiona prawdziwym klientem HTTP po publikacji docs/api/ przez backend.
 */
export interface OfertyApi {
  szukaj(filtry: FiltryWyszukiwania): Promise<WynikWyszukiwania>
  pobierzSzczegoly(id: string): Promise<Oferta | null>
}
