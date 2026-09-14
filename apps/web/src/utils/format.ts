import { JEDNOSTKA_CENY_ETYKIETY, type JednostkaCeny } from '../types/oferta'

export function formatujCene(
  cena: string | null,
  waluta: string,
  jednostka: JednostkaCeny | null,
  cenaOd: boolean,
): string {
  if (cena == null) return 'Cena nie ustalona'
  const liczba = Number(cena)
  const kwota = new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency: waluta || 'PLN',
    minimumFractionDigits: liczba % 1 === 0 ? 0 : 2,
  }).format(liczba)
  const jednostkaTekst = jednostka ? ` ${JEDNOSTKA_CENY_ETYKIETY[jednostka]}` : ''
  return `${cenaOd ? 'od ' : ''}${kwota}${jednostkaTekst}`
}

export function formatujDate(iso: string | null): string {
  if (!iso) return 'nie ustalono'
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) return 'nie ustalono'
  return new Intl.DateTimeFormat('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(data)
}

export function formatujDatePobrania(iso: string): string {
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) return 'nieznana'
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(data)
}

export function formatujTermin(od: string | null, doD: string | null): string {
  if (!od && !doD) return 'termin nie ustalony'
  if (od && doD) return `${formatujDate(od)} – ${formatujDate(doD)}`
  return `od ${formatujDate(od)}`
}

export function formatujTakNie(wartosc: boolean | null): string {
  if (wartosc === true) return 'Tak'
  if (wartosc === false) return 'Nie'
  return 'nie ustalono'
}
