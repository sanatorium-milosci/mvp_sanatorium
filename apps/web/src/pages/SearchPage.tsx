import { useEffect, useState } from 'react'
import { ofertyApi, type FiltryWyszukiwania } from '../api'
import { OfferList } from '../components/OfferList'
import { SearchFilters } from '../components/SearchFilters'
import { StanBledu, StanBrakWynikow, StanLadowania } from '../components/StanyWidoku'
import type { Oferta } from '../types/oferta'

export function SearchPage() {
  const [filtry, setFiltry] = useState<FiltryWyszukiwania>({})
  const [oferty, setOferty] = useState<Oferta[] | null>(null)
  const [razem, setRazem] = useState(0)
  const [stronRazem, setStronRazem] = useState(1)
  const [ladowanie, setLadowanie] = useState(true)
  const [blad, setBlad] = useState<string | null>(null)
  const [licznikProby, setLicznikProby] = useState(0)
  const [miejscowosci, setMiejscowosci] = useState<string[]>([])

  useEffect(() => {
    ofertyApi
      .pobierzFiltry()
      .then((slowniki) => setMiejscowosci(slowniki.miejscowosci))
      .catch(() => {
        // Nieistotne dla działania wyszukiwarki — filtr miejscowości po prostu zostanie pusty.
      })
  }, [])

  useEffect(() => {
    let aktualne = true
    setLadowanie(true)
    setBlad(null)

    ofertyApi
      .szukaj(filtry)
      .then((wynik) => {
        if (!aktualne) return
        setOferty(wynik.elementy)
        setRazem(wynik.stronicowanie.razem)
        setStronRazem(wynik.stronicowanie.stron_razem)
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

  const strona = filtry.strona ?? 1

  return (
    <div className="strona-wyszukiwania">
      <SearchFilters
        filtry={filtry}
        miejscowosci={miejscowosci}
        onZmiana={(nowe) => setFiltry({ ...nowe, strona: undefined })}
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
              Znaleziono {razem} {razem === 1 ? 'ofertę' : 'ofert'}
            </p>
            <OfferList oferty={oferty} />
            {stronRazem > 1 && (
              <div className="stronicowanie">
                <button
                  type="button"
                  disabled={strona <= 1}
                  onClick={() => setFiltry({ ...filtry, strona: strona - 1 })}
                >
                  ← Poprzednia
                </button>
                <span>
                  Strona {strona} z {stronRazem}
                </span>
                <button
                  type="button"
                  disabled={strona >= stronRazem}
                  onClick={() => setFiltry({ ...filtry, strona: strona + 1 })}
                >
                  Następna →
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}
