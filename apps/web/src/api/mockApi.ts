import type { ListaOfert, Oferta, SlownikiFiltrow } from '../types/oferta'
import { OFERTY_MOCK } from './mockData'
import type { FiltryWyszukiwania, OfertyApi } from './types'

const OPOZNIENIE_MS = 300
const NA_STRONIE_DOMYSLNIE = 20

const opoznij = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function pasujeDoFiltrow(oferta: Oferta, filtry: FiltryWyszukiwania): boolean {
  if (filtry.q) {
    const fraza = filtry.q.trim().toLowerCase()
    const pola = [oferta.osrodek.nazwa, oferta.osrodek.miejscowosc, oferta.pakiet.nazwa]
    if (fraza && !pola.some((p) => p.toLowerCase().includes(fraza))) return false
  }
  if (filtry.miejscowosc && oferta.osrodek.miejscowosc !== filtry.miejscowosc) return false
  if (filtry.wojewodztwo && oferta.osrodek.wojewodztwo !== filtry.wojewodztwo) return false
  if (filtry.profil && !oferta.profile.includes(filtry.profil)) return false
  if (filtry.wyzywienie && oferta.standard.wyzywienie !== filtry.wyzywienie) return false
  if (filtry.typ_pokoju && oferta.standard.typ_pokoju !== filtry.typ_pokoju) return false
  if (filtry.jednostka_ceny && oferta.cena.jednostka !== filtry.jednostka_ceny) return false
  if (filtry.cena_min != null) {
    if (oferta.cena.wartosc == null || Number(oferta.cena.wartosc) < filtry.cena_min) return false
  }
  if (filtry.cena_max != null) {
    if (oferta.cena.wartosc == null || Number(oferta.cena.wartosc) > filtry.cena_max) return false
  }
  if (filtry.min_dni != null) {
    if (oferta.pakiet.liczba_dni == null || oferta.pakiet.liczba_dni < filtry.min_dni) return false
  }
  if (filtry.max_dni != null) {
    if (oferta.pakiet.liczba_dni == null || oferta.pakiet.liczba_dni > filtry.max_dni) return false
  }
  if (filtry.termin_od) {
    if (!oferta.pakiet.termin_od || oferta.pakiet.termin_od < filtry.termin_od) return false
  }
  if (filtry.termin_do) {
    if (!oferta.pakiet.termin_do || oferta.pakiet.termin_do > filtry.termin_do) return false
  }
  if (filtry.tylko_dostepne && oferta.pakiet.dostepny !== true) return false
  if (!filtry.pokaz_przeszle) {
    const dzisiaj = new Date().toISOString().slice(0, 10)
    if (oferta.pakiet.termin_do && oferta.pakiet.termin_do < dzisiaj) return false
  }
  if (filtry.basen && oferta.udogodnienia.basen !== true) return false
  if (filtry.winda && oferta.udogodnienia.winda !== true) return false
  if (filtry.parking && oferta.udogodnienia.parking !== true) return false
  if (filtry.zwierzeta && oferta.udogodnienia.zwierzeta !== true) return false
  if (filtry.dostepny_dla_wozka && oferta.udogodnienia.dostepny_dla_wozka !== true) return false
  return true
}

function posortuj(oferty: Oferta[], sortuj: FiltryWyszukiwania['sortuj']): Oferta[] {
  const posortowane = [...oferty]
  const cenaLubNieskonczonosc = (o: Oferta) => (o.cena.wartosc != null ? Number(o.cena.wartosc) : Infinity)
  const dniLubNieskonczonosc = (o: Oferta) => o.pakiet.liczba_dni ?? Infinity
  switch (sortuj) {
    case 'cena_asc':
      return posortowane.sort((a, b) => cenaLubNieskonczonosc(a) - cenaLubNieskonczonosc(b))
    case 'cena_desc':
      return posortowane.sort((a, b) => cenaLubNieskonczonosc(b) - cenaLubNieskonczonosc(a))
    case 'dni_asc':
      return posortowane.sort((a, b) => dniLubNieskonczonosc(a) - dniLubNieskonczonosc(b))
    case 'dni_desc':
      return posortowane.sort((a, b) => dniLubNieskonczonosc(b) - dniLubNieskonczonosc(a))
    case 'termin_od_asc':
      return posortowane.sort((a, b) =>
        (a.pakiet.termin_od ?? '9999-99-99').localeCompare(b.pakiet.termin_od ?? '9999-99-99'),
      )
    default:
      return posortowane
  }
}

/**
 * Implementacja tymczasowa działająca na danych mockowych, zgodna z kształtem
 * odpowiedzi z docs/api/specyfikacja.md. Docelowo do podmiany na httpApi.ts
 * (patrz src/api/index.ts).
 */
export const mockOfertyApi: OfertyApi = {
  async szukaj(filtry: FiltryWyszukiwania): Promise<ListaOfert> {
    await opoznij(OPOZNIENIE_MS)
    const dopasowane = posortuj(OFERTY_MOCK.filter((oferta) => pasujeDoFiltrow(oferta, filtry)), filtry.sortuj)

    const naStronie = filtry.na_stronie ?? NA_STRONIE_DOMYSLNIE
    const strona = filtry.strona ?? 1
    const start = (strona - 1) * naStronie
    const elementy = dopasowane.slice(start, start + naStronie)

    return {
      elementy,
      stronicowanie: {
        strona,
        na_stronie: naStronie,
        razem: dopasowane.length,
        stron_razem: Math.max(1, Math.ceil(dopasowane.length / naStronie)),
      },
    }
  },

  async pobierzSzczegoly(id: string): Promise<Oferta | null> {
    await opoznij(OPOZNIENIE_MS)
    return OFERTY_MOCK.find((oferta) => String(oferta.id) === id) ?? null
  },

  async pobierzFiltry(): Promise<SlownikiFiltrow> {
    await opoznij(OPOZNIENIE_MS)
    const unikalne = <T,>(wartosci: (T | null | undefined)[]) =>
      Array.from(new Set(wartosci.filter((w): w is T => w != null)))

    const ceny = unikalne(OFERTY_MOCK.map((o) => o.cena.wartosc)).map(Number)
    const dni = unikalne(OFERTY_MOCK.map((o) => o.pakiet.liczba_dni))

    return {
      miejscowosci: unikalne(OFERTY_MOCK.map((o) => o.osrodek.miejscowosc)).sort((a, b) => a.localeCompare(b, 'pl')),
      wojewodztwa: unikalne(OFERTY_MOCK.map((o) => o.osrodek.wojewodztwo)).sort((a, b) => a.localeCompare(b, 'pl')),
      profile: unikalne(OFERTY_MOCK.flatMap((o) => o.profile)),
      wyzywienie: unikalne(OFERTY_MOCK.map((o) => o.standard.wyzywienie)),
      typy_pokoju: unikalne(OFERTY_MOCK.map((o) => o.standard.typ_pokoju)),
      jednostki_ceny: unikalne(OFERTY_MOCK.map((o) => o.cena.jednostka)),
      cena_min: ceny.length ? Math.min(...ceny).toFixed(2) : null,
      cena_max: ceny.length ? Math.max(...ceny).toFixed(2) : null,
      min_dni: dni.length ? Math.min(...dni) : null,
      max_dni: dni.length ? Math.max(...dni) : null,
      liczba_ofert_razem: OFERTY_MOCK.length,
    }
  },
}
