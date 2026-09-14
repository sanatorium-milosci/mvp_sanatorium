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

  const { osrodek, pakiet, cena, standard, udogodnienia, linki } = oferta

  return (
    <article className="szczegoly-oferty">
      <Link to="/" className="szczegoly-oferty__powrot">
        ← Wróć do wyników
      </Link>

      <header>
        <h1>{osrodek.nazwa}</h1>
        <p className="szczegoly-oferty__miejscowosc">
          {osrodek.miejscowosc}
          {osrodek.wojewodztwo ? `, woj. ${osrodek.wojewodztwo}` : ''}
        </p>
        <h2>{pakiet.nazwa}</h2>
      </header>

      <section className="szczegoly-oferty__cena-blok">
        <p className="szczegoly-oferty__cena">{formatujCene(cena.wartosc, cena.waluta, cena.jednostka, cena.cena_od)}</p>
        {pakiet.dostepny === false && <span className="etykieta etykieta--brak">Brak miejsc</span>}
        {pakiet.dostepny === true && <span className="etykieta etykieta--ok">Dostępne</span>}
      </section>

      {cena.szacowany_koszt_calkowity != null && (
        <p className="szczegoly-oferty__koszt-calkowity">
          Szacowany koszt całego pobytu: <strong>{formatujCene(cena.szacowany_koszt_calkowity, cena.waluta, null, false)}</strong>
        </p>
      )}

      <dl className="szczegoly-oferty__lista">
        <div>
          <dt>Termin</dt>
          <dd>{formatujTermin(pakiet.termin_od, pakiet.termin_do)}</dd>
        </div>
        <div>
          <dt>Długość pobytu</dt>
          <dd>
            {pakiet.liczba_dni != null ? `${pakiet.liczba_dni} dni` : 'nie ustalono'}
            {pakiet.liczba_nocy != null ? ` (${pakiet.liczba_nocy} nocy)` : ''}
          </dd>
        </div>
        <div>
          <dt>Wyżywienie</dt>
          <dd>{standard.wyzywienie ? WYZYWIENIE_ETYKIETY[standard.wyzywienie] : 'nie ustalono'}</dd>
        </div>
        <div>
          <dt>Typ pokoju</dt>
          <dd>{standard.typ_pokoju ? TYP_POKOJU_ETYKIETY[standard.typ_pokoju] : 'nie ustalono'}</dd>
        </div>
        {cena.doplata_jedynka != null && (
          <div>
            <dt>Dopłata za jedynkę</dt>
            <dd>{formatujCene(cena.doplata_jedynka, cena.waluta, null, false)}</dd>
          </div>
        )}
        <div>
          <dt>Opieka lekarska</dt>
          <dd>{formatujTakNie(standard.opieka_lekarska)}</dd>
        </div>
        {standard.liczba_zabiegow_dziennie != null && (
          <div>
            <dt>Zabiegi dziennie</dt>
            <dd>{standard.liczba_zabiegow_dziennie}</dd>
          </div>
        )}
      </dl>

      {standard.zabiegi.length > 0 && (
        <section>
          <h3>Zabiegi w ofercie</h3>
          <ul className="szczegoly-oferty__tagi">
            {standard.zabiegi.map((z) => (
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
        {osrodek.telefon && (
          <p>
            Telefon: <a href={`tel:${osrodek.telefon}`}>{osrodek.telefon}</a>
          </p>
        )}
        <p>
          <a href={linki.url_zrodla} target="_blank" rel="noopener noreferrer">
            Zobacz stronę ośrodka ↗
          </a>
        </p>
        {linki.url_rezerwacji && (
          <p>
            <a href={linki.url_rezerwacji} target="_blank" rel="noopener noreferrer" className="przycisk-glowny">
              Przejdź do rezerwacji ↗
            </a>
          </p>
        )}
        <p className="szczegoly-oferty__pobrano">
          Dane pobrane: {formatujDatePobrania(linki.pobrano_o)}. Sprawdź aktualność ceny i dostępności bezpośrednio
          u ośrodka.
        </p>
      </section>
    </article>
  )
}
