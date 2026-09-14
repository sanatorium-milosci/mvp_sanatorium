import { useEffect, useMemo, useState } from 'react'
import { ofertyApi, type FiltryWyszukiwania } from '../api'
import { OFERTY_MOCK } from '../api/mockData'
import { OfferList } from '../components/OfferList'
import { SearchFilters } from '../components/SearchFilters'
import { StanBledu, StanBrakWynikow, StanLadowania } from '../components/StanyWidoku'
import type { Oferta } from '../types/oferta'

export function SearchPage() {
  const [filtry, setFiltry] = useState<FiltryWyszukiwania>({})
  const [oferty, setOferty] = useState<Oferta[] | null>(null)
  const [ladowanie, setLadowanie] = useState(true)
  const [blad, setBlad] = useState<string | null>(null)
  const [licznikProby, setLicznikProby] = useState(0)

  const miejscowosci = useMemo(
    () => Array.from(new Set(OFERTY_MOCK.map((o) => o.miejscowosc))).sort((a, b) => a.localeCompare(b, 'pl')),
    [],
  )

  useEffect(() => {
    let aktualne = true
    setLadowanie(true)
    setBlad(null)

    ofertyApi
      .szukaj(filtry)
      .then((wynik) => {
        if (!aktualne) return
        setOferty(wynik.oferty)
      })
      .catch((err: unknown) => {
        if (!aktualne) return
        setBlad(err instanceof Error ? err.message : 'Nieznany błąd')
      })
      .finally(() => {
        if (aktualne) setLadowanie(false)
      })

    return () => {
      aktualne = false
    }
  }, [filtry, licznikProby])

  return (
    <div className="strona-wyszukiwania">
      <SearchFilters
        filtry={filtry}
        miejscowosci={miejscowosci}
        onZmiana={setFiltry}
        onWyczysc={() => setFiltry({})}
      />

      <section className="wyniki" aria-live="polite">
        {ladowanie && <StanLadowania />}
        {!ladowanie && blad && (
          <StanBledu komunikat={blad} onPonow={() => setLicznikProby((n) => n + 1)} />
        )}
        {!ladowanie && !blad && oferty && oferty.length === 0 && <StanBrakWynikow />}
        {!ladowanie && !blad && oferty && oferty.length > 0 && (
          <>
            <p className="wyniki__liczba">
              Znaleziono {oferty.length} {oferty.length === 1 ? 'ofertę' : 'ofert'}
            </p>
            <OfferList oferty={oferty} />
          </>
        )}
      </section>
    </div>
  )
}
