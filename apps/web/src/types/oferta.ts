// Lustrzane odbicie packages/core/models.py — kontrakt Oferta, wersja 0.1.0.
// Zmiany tego pliku muszą iść w parze ze zmianami kontraktu w packages/core/models.py.

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

export interface Zrodlo {
  url: string
  pobrano_o: string // ISO datetime
  adapter: string
  wersja_adaptera: string
  hash_tresci: string
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

export interface Oferta {
  // --- identyfikacja ---
  adapter: string
  zrodlo_id: string

  // --- ośrodek ---
  osrodek_klucz: string
  osrodek_nazwa: string
  miejscowosc: string
  wojewodztwo: string | null
  nip: string | null

  // --- pobyt ---
  nazwa_pakietu: string
  liczba_dni: number | null
  liczba_nocy: number | null
  termin_od: string | null // ISO date
  termin_do: string | null // ISO date
  dostepny: boolean | null

  // --- cena ---
  cena: string | null // Decimal jako string, bez utraty precyzji
  jednostka_ceny: JednostkaCeny | null
  waluta: string
  cena_od: boolean

  // --- co w cenie ---
  wyzywienie: Wyzywienie | null
  typ_pokoju: TypPokoju | null
  doplata_jedynka: string | null
  liczba_zabiegow_dziennie: number | null
  zabiegi: string[]
  opieka_lekarska: boolean | null
  oplata_klimatyczna_doba: string | null

  // --- klasyfikacja ---
  profile: ProfilLeczniczy[]

  // --- reszta ---
  udogodnienia: Udogodnienia
  telefon: string | null
  url_rezerwacji: string | null
  zrodlo: Zrodlo

  // --- identyfikator dla frontendu (nadawany przez backend/mock) ---
  id: string
}
