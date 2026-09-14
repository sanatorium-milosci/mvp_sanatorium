import type { Oferta } from '../types/oferta'
import { OFERTY_MOCK } from './mockData'
import type { FiltryWyszukiwania, OfertyApi, WynikWyszukiwania } from './types'

const OPOZNIENIE_MS = 300

const opoznij = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function pasujeDoFiltrow(oferta: Oferta, filtry: FiltryWyszukiwania): boolean {
  if (filtry.fraza) {
    const fraza = filtry.fraza.trim().toLowerCase()
    const pola = [oferta.osrodek_nazwa, oferta.miejscowosc, oferta.nazwa_pakietu]
    if (fraza && !pola.some((p) => p.toLowerCase().includes(fraza))) return false
  }
  if (filtry.miejscowosc && oferta.miejscowosc !== filtry.miejscowosc) return false
  if (filtry.profil && !oferta.profile.includes(filtry.profil)) return false
  if (filtry.wyzywienie && oferta.wyzywienie !== filtry.wyzywienie) return false
  if (filtry.jednostkaCeny && oferta.jednostka_ceny !== filtry.jednostkaCeny) return false
  if (filtry.cenaMax != null) {
    if (oferta.cena == null) return false
    if (Number(oferta.cena) > filtry.cenaMax) return false
  }
  if (filtry.terminOd) {
    if (!oferta.termin_od) return false
    if (oferta.termin_od < filtry.terminOd) return false
  }
  if (filtry.terminDo) {
    if (!oferta.termin_do) return false
    if (oferta.termin_do > filtry.terminDo) return false
  }
  if (filtry.tylkoDostepne && oferta.dostepny !== true) return false
  return true
}

/**
 * Implementacja tymczasowa działająca na danych mockowych.
 * Docelowo do podmiany na klienta HTTP wg kontraktu z docs/api/ (patrz README apps/web).
 */
export const mockOfertyApi: OfertyApi = {
  async szukaj(filtry: FiltryWyszukiwania): Promise<WynikWyszukiwania> {
    await opoznij(OPOZNIENIE_MS)
    const wynik = OFERTY_MOCK.filter((oferta) => pasujeDoFiltrow(oferta, filtry))
    return { oferty: wynik, liczbaWszystkich: wynik.length }
  },

  async pobierzSzczegoly(id: string): Promise<Oferta | null> {
    await opoznij(OPOZNIENIE_MS)
    return OFERTY_MOCK.find((oferta) => oferta.id === id) ?? null
  },
}
