// Typy TS zgodne z realnym kontraktem API: docs/api/specyfikacja.md (backend, wersja kontraktu 0.1.0).
// Odzwierciedlają odpowiedź JSON z GET /api/v1/oferty i GET /api/v1/oferty/{id}.

export const WERSJA_KONTRAKTU = '0.1.0'

export type ProfilLeczniczy =
  | 'ortopedyczno_urazowy'
  | 'reumatologiczny'
  | 'kardiologiczny'
  | 'naczyn_obwodowych'
  | 'gorne_drogi_oddechowe'
  | 'dolne_drogi_oddechowe'
  | 'uklad_trawienia'
  | 'endokrynologiczny'
  | 'cukrzyca'
  | 'otylosc'
  | 'osteoporoza'
  | 'neurologiczny'
  | 'nerki_drogi_moczowe'
  | 'skora'
  | 'kobiecy'
  | 'psychiczny'
  | 'nieznany'

export const PROFILE_LECZNICZE_ETYKIETY: Record<ProfilLeczniczy, string> = {
  ortopedyczno_urazowy: 'Ortopedyczno-urazowy',
  reumatologiczny: 'Reumatologiczny',
  kardiologiczny: 'Kardiologiczny',
  naczyn_obwodowych: 'Naczyń obwodowych',
  gorne_drogi_oddechowe: 'Górnych dróg oddechowych',
  dolne_drogi_oddechowe: 'Dolnych dróg oddechowych',
  uklad_trawienia: 'Układu trawienia',
  endokrynologiczny: 'Endokrynologiczny',
  cukrzyca: 'Cukrzyca',
  otylosc: 'Otyłość',
  osteoporoza: 'Osteoporoza',
  neurologiczny: 'Neurologiczny',
  nerki_drogi_moczowe: 'Nerek i dróg moczowych',
  skora: 'Skóra',
  kobiecy: 'Kobiecy',
  psychiczny: 'Psychiczny',
  nieznany: 'Nieznany',
}

export type JednostkaCeny = 'osobodoba' | 'turnus_osoba' | 'pokoj_doba'

export const JEDNOSTKA_CENY_ETYKIETY: Record<JednostkaCeny, string> = {
  osobodoba: 'za osobodobę',
  turnus_osoba: 'za turnus / os.',
  pokoj_doba: 'za pokój / doba',
}

export type TypPokoju = 'jednoosobowy' | 'dwuosobowy' | 'apartament' | 'studio' | 'inny'

export const TYP_POKOJU_ETYKIETY: Record<TypPokoju, string> = {
  jednoosobowy: 'Jednoosobowy',
  dwuosobowy: 'Dwuosobowy',
  apartament: 'Apartament',
  studio: 'Studio',
  inny: 'Inny',
}

export type Wyzywienie = 'brak' | 'sniadania' | 'hb' | 'fb' | 'all_inclusive'

export const WYZYWIENIE_ETYKIETY: Record<Wyzywienie, string> = {
  brak: 'Bez wyżywienia',
  sniadania: 'Śniadania',
  hb: 'Dwa posiłki (HB)',
  fb: 'Trzy posiłki (FB)',
  all_inclusive: 'All inclusive',
}

export interface Osrodek {
  klucz: string
  nazwa: string
  miejscowosc: string
  wojewodztwo: string | null
  nip: string | null
  telefon: string | null
}

export interface Pakiet {
  nazwa: string
  liczba_dni: number | null
  liczba_nocy: number | null
  termin_od: string | null // ISO date
  termin_do: string | null // ISO date
  dostepny: boolean | null
}

export interface Cena {
  wartosc: string | null // Decimal jako string, np. "2980.00"
  waluta: string
  jednostka: JednostkaCeny | null
  cena_od: boolean
  /** Liczony przez backend tylko gdy dane jednoznacznie na to pozwalają, inaczej null. */
  szacowany_koszt_calkowity: string | null
  doplata_jedynka: string | null
  oplata_klimatyczna_doba: string | null
}

export interface Standard {
  wyzywienie: Wyzywienie | null
  typ_pokoju: TypPokoju | null
  liczba_zabiegow_dziennie: number | null
  zabiegi: string[]
  opieka_lekarska: boolean | null
}

export interface Udogodnienia {
  winda: boolean | null
  dostepny_dla_wozka: boolean | null
  parking: boolean | null
  parking_platny: boolean | null
  wifi: boolean | null
  basen: boolean | null
  zwierzeta: boolean | null
  odleglosc_od_centrum_m: number | null
}

export interface Linki {
  url_rezerwacji: string | null
  url_zrodla: string
  pobrano_o: string // ISO datetime
}

export interface Oferta {
  id: number
  adapter: string
  zrodlo_id: string
  osrodek: Osrodek
  pakiet: Pakiet
  cena: Cena
  standard: Standard
  profile: ProfilLeczniczy[]
  udogodnienia: Udogodnienia
  linki: Linki
}

export interface Stronicowanie {
  strona: number
  na_stronie: number
  razem: number
  stron_razem: number
}

export interface ListaOfert {
  elementy: Oferta[]
  stronicowanie: Stronicowanie
}

/** Odpowiedź GET /api/v1/filtry — słowniki aktualnie dostępnych wariantów filtrów. */
export interface SlownikiFiltrow {
  miejscowosci: string[]
  wojewodztwa: string[]
  profile: ProfilLeczniczy[]
  wyzywienie: Wyzywienie[]
  typy_pokoju: TypPokoju[]
  jednostki_ceny: JednostkaCeny[]
  cena_min: string | null
  cena_max: string | null
  min_dni: number | null
  max_dni: number | null
  liczba_ofert_razem: number
}
