import { Link } from 'react-router-dom'
import type { Oferta } from '../types/oferta'
import { formatujCene, formatujDatePobrania, formatujTermin } from '../utils/format'

interface Props {
  oferta: Oferta
}

export function OfferCard({ oferta }: Props) {
  return (
    <li className="karta-oferty">
      <Link to={`/oferta/${oferta.id}`} className="karta-oferty__link">
        <div className="karta-oferty__naglowek">
          <h3>{oferta.osrodek.nazwa}</h3>
          <span className="karta-oferty__miejscowosc">{oferta.osrodek.miejscowosc}</span>
        </div>
        <p className="karta-oferty__pakiet">{oferta.pakiet.nazwa}</p>
        <p className="karta-oferty__termin">{formatujTermin(oferta.pakiet.termin_od, oferta.pakiet.termin_do)}</p>
        <div className="karta-oferty__stopka">
          <span className="karta-oferty__cena">
            {formatujCene(oferta.cena.wartosc, oferta.cena.waluta, oferta.cena.jednostka, oferta.cena.cena_od)}
          </span>
          {oferta.pakiet.dostepny === false && <span className="etykieta etykieta--brak">Brak miejsc</span>}
          {oferta.pakiet.dostepny === true && <span className="etykieta etykieta--ok">Dostępne</span>}
        </div>
        <p className="karta-oferty__pobrano">Dane pobrane: {formatujDatePobrania(oferta.linki.pobrano_o)}</p>
      </Link>
    </li>
  )
}
