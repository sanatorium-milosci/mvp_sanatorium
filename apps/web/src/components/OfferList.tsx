import type { Oferta } from '../types/oferta'
import { OfferCard } from './OfferCard'

interface Props {
  oferty: Oferta[]
}

export function OfferList({ oferty }: Props) {
  return (
    <ul className="lista-ofert" aria-label="Wyniki wyszukiwania">
      {oferty.map((oferta) => (
        <OfferCard key={oferta.id} oferta={oferta} />
      ))}
    </ul>
  )
}
