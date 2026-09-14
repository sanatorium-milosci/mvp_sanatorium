import type { ListaOfert, Oferta, SlownikiFiltrow } from '../types/oferta'
import { BladApi, type FiltryWyszukiwania, type OfertyApi } from './types'

/**
 * Klient HTTP zgodny z docs/api/specyfikacja.md (GET /api/v1/oferty,
 * /api/v1/oferty/{id}, /api/v1/filtry). Włączany przez src/api/index.ts,
 * gdy ustawione jest VITE_API_BASE_URL.
 */
export function createHttpOfertyApi(baseUrl: string): OfertyApi {
  const url = (sciezka: string, parametry?: Record<string, unknown> | FiltryWyszukiwania) => {
    const pelny = new URL(`${baseUrl.replace(/\/$/, '')}/api/v1${sciezka}`)
    for (const [klucz, wartosc] of Object.entries(parametry ?? {})) {
      if (wartosc === undefined || wartosc === null || wartosc === '') continue
      pelny.searchParams.set(klucz, String(wartosc))
    }
    return pelny.toString()
  }

  async function pobierzJson<T>(adres: string): Promise<T> {
    let odpowiedz: Response
    try {
      odpowiedz = await fetch(adres)
    } catch {
      throw new BladApi('Brak połączenia z serwerem. Sprawdź internet i spróbuj ponownie.')
    }
    if (!odpowiedz.ok) {
      if (odpowiedz.status === 404) throw new BladApi('Nie znaleziono zasobu.')
      throw new BladApi(`Serwer zwrócił błąd (${odpowiedz.status}). Spróbuj ponownie później.`)
    }
    return (await odpowiedz.json()) as T
  }

  return {
    async szukaj(filtry: FiltryWyszukiwania): Promise<ListaOfert> {
      return pobierzJson<ListaOfert>(url('/oferty', filtry))
    },

    async pobierzSzczegoly(id: string): Promise<Oferta | null> {
      try {
        return await pobierzJson<Oferta>(url(`/oferty/${encodeURIComponent(id)}`))
      } catch (err) {
        if (err instanceof BladApi && err.message === 'Nie znaleziono zasobu.') return null
        throw err
      }
    },

    async pobierzFiltry(): Promise<SlownikiFiltrow> {
      return pobierzJson<SlownikiFiltrow>(url('/filtry'))
    },
  }
}
