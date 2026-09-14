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
          <h3>{oferta.osrodek_nazwa}</h3>
          <span className="karta-oferty__miejscowosc">{oferta.miejscowosc}</span>
        </div>
        <p className="karta-oferty__pakiet">{oferta.nazwa_pakietu}</p>
        <p className="karta-oferty__termin">{formatujTermin(oferta.termin_od, oferta.termin_do)}</p>
        <div className="karta-oferty__stopka">
          <span className="karta-oferty__cena">
            {formatujCene(oferta.cena, oferta.waluta, oferta.jednostka_ceny, oferta.cena_od)}
          </span>
          {oferta.dostepny === false && <span className="etykieta etykieta--brak">Brak miejsc</span>}
          {oferta.dostepny === true && <span className="etykieta etykieta--ok">Dostępne</span>}
        </div>
        <p className="karta-oferty__pobrano">Dane pobrane: {formatujDatePobrania(oferta.zrodlo.pobrano_o)}</p>
      </Link>
    </li>
  )
}
