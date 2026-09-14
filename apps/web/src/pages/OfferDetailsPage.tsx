import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ofertyApi } from '../api'
import { StanBledu, StanLadowania } from '../components/StanyWidoku'
import {
  PROFILE_LECZNICZE_ETYKIETY,
  TYP_POKOJU_ETYKIETY,
  WYZYWIENIE_ETYKIETY,
  type Oferta,
} from '../types/oferta'
import { formatujCene, formatujDatePobrania, formatujTakNie, formatujTermin } from '../utils/format'

export function OfferDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const [oferta, setOferta] = useState<Oferta | null | undefined>(undefined)
  const [blad, setBlad] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let aktualne = true
    setOferta(undefined)
    setBlad(null)

    ofertyApi
      .pobierzSzczegoly(id)
      .then((wynik) => {
        if (aktualne) setOferta(wynik)
      })
      .catch((err: unknown) => {
        if (aktualne) setBlad(err instanceof Error ? err.message : 'Nieznany błąd')
      })

    return () => {
      aktualne = false
    }
  }, [id])

  if (blad) return <StanBledu komunikat={blad} />
  if (oferta === undefined) return <StanLadowania />

  if (oferta === null) {
    return (
      <div className="stan-widoku" role="alert">
        <p>Nie znaleziono oferty.</p>
        <Link to="/">Wróć do wyszukiwarki</Link>
      </div>
    )
  }

  const { udogodnienia } = oferta

  return (
    <article className="szczegoly-oferty">
      <Link to="/" className="szczegoly-oferty__powrot">
        ← Wróć do wyników
      </Link>

      <header>
        <h1>{oferta.osrodek_nazwa}</h1>
        <p className="szczegoly-oferty__miejscowosc">
          {oferta.miejscowosc}
          {oferta.wojewodztwo ? `, woj. ${oferta.wojewodztwo}` : ''}
        </p>
        <h2>{oferta.nazwa_pakietu}</h2>
      </header>

      <section className="szczegoly-oferty__cena-blok">
        <p className="szczegoly-oferty__cena">
          {formatujCene(oferta.cena, oferta.waluta, oferta.jednostka_ceny, oferta.cena_od)}
        </p>
        {oferta.dostepny === false && <span className="etykieta etykieta--brak">Brak miejsc</span>}
        {oferta.dostepny === true && <span className="etykieta etykieta--ok">Dostępne</span>}
      </section>

      <dl className="szczegoly-oferty__lista">
        <div>
          <dt>Termin</dt>
          <dd>{formatujTermin(oferta.termin_od, oferta.termin_do)}</dd>
        </div>
        <div>
          <dt>Długość pobytu</dt>
          <dd>
            {oferta.liczba_dni != null ? `${oferta.liczba_dni} dni` : 'nie ustalono'}
            {oferta.liczba_nocy != null ? ` (${oferta.liczba_nocy} nocy)` : ''}
          </dd>
        </div>
        <div>
          <dt>Wyżywienie</dt>
          <dd>{oferta.wyzywienie ? WYZYWIENIE_ETYKIETY[oferta.wyzywienie] : 'nie ustalono'}</dd>
        </div>
        <div>
          <dt>Typ pokoju</dt>
          <dd>{oferta.typ_pokoju ? TYP_POKOJU_ETYKIETY[oferta.typ_pokoju] : 'nie ustalono'}</dd>
        </div>
        {oferta.doplata_jedynka != null && (
          <div>
            <dt>Dopłata za jedynkę</dt>
            <dd>{formatujCene(oferta.doplata_jedynka, oferta.waluta, null, false)}</dd>
          </div>
        )}
        <div>
          <dt>Opieka lekarska</dt>
          <dd>{formatujTakNie(oferta.opieka_lekarska)}</dd>
        </div>
        {oferta.liczba_zabiegow_dziennie != null && (
          <div>
            <dt>Zabiegi dziennie</dt>
            <dd>{oferta.liczba_zabiegow_dziennie}</dd>
          </div>
        )}
      </dl>

      {oferta.zabiegi.length > 0 && (
        <section>
          <h3>Zabiegi w ofercie</h3>
          <ul className="szczegoly-oferty__tagi">
            {oferta.zabiegi.map((z) => (
              <li key={z}>{z}</li>
            ))}
          </ul>
        </section>
      )}

      {oferta.profile.length > 0 && (
        <section>
          <h3>Profile lecznicze</h3>
          <ul className="szczegoly-oferty__tagi">
            {oferta.profile.map((p) => (
              <li key={p}>{PROFILE_LECZNICZE_ETYKIETY[p]}</li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3>Udogodnienia</h3>
        <dl className="szczegoly-oferty__lista">
          <div>
            <dt>Winda</dt>
            <dd>{formatujTakNie(udogodnienia.winda)}</dd>
          </div>
          <div>
            <dt>Dostępność dla wózka</dt>
            <dd>{formatujTakNie(udogodnienia.dostepny_dla_wozka)}</dd>
          </div>
          <div>
            <dt>Parking</dt>
            <dd>
              {formatujTakNie(udogodnienia.parking)}
              {udogodnienia.parking && udogodnienia.parking_platny != null
                ? ` (${udogodnienia.parking_platny ? 'płatny' : 'bezpłatny'})`
                : ''}
            </dd>
          </div>
          <div>
            <dt>WiFi</dt>
            <dd>{formatujTakNie(udogodnienia.wifi)}</dd>
          </div>
          <div>
            <dt>Basen</dt>
            <dd>{formatujTakNie(udogodnienia.basen)}</dd>
          </div>
          <div>
            <dt>Zwierzęta</dt>
            <dd>{formatujTakNie(udogodnienia.zwierzeta)}</dd>
          </div>
          {udogodnienia.odleglosc_od_centrum_m != null && (
            <div>
              <dt>Odległość od centrum</dt>
              <dd>{udogodnienia.odleglosc_od_centrum_m} m</dd>
            </div>
          )}
        </dl>
      </section>

      <section className="szczegoly-oferty__kontakt">
        <h3>Kontakt i źródło</h3>
        {oferta.telefon && (
          <p>
            Telefon: <a href={`tel:${oferta.telefon}`}>{oferta.telefon}</a>
          </p>
        )}
        <p>
          <a href={oferta.zrodlo.url} target="_blank" rel="noopener noreferrer">
            Zobacz stronę ośrodka ↗
          </a>
        </p>
        {oferta.url_rezerwacji && (
          <p>
            <a href={oferta.url_rezerwacji} target="_blank" rel="noopener noreferrer" className="przycisk-glowny">
              Przejdź do rezerwacji ↗
            </a>
          </p>
        )}
        <p className="szczegoly-oferty__pobrano">
          Dane pobrane: {formatujDatePobrania(oferta.zrodlo.pobrano_o)}. Sprawdź aktualność ceny i dostępności
          bezpośrednio u ośrodka.
        </p>
      </section>
    </article>
  )
}
