import type { FiltryWyszukiwania, Sortowanie } from '../api'
import { PROFILE_LECZNICZE_ETYKIETY, WYZYWIENIE_ETYKIETY, type ProfilLeczniczy, type Wyzywienie } from '../types/oferta'

interface Props {
  filtry: FiltryWyszukiwania
  miejscowosci: string[]
  onZmiana: (filtry: FiltryWyszukiwania) => void
  onWyczysc: () => void
}

const PROFILE_OPCJE = Object.entries(PROFILE_LECZNICZE_ETYKIETY) as [ProfilLeczniczy, string][]
const WYZYWIENIE_OPCJE = Object.entries(WYZYWIENIE_ETYKIETY) as [Wyzywienie, string][]

const SORTOWANIE_ETYKIETY: Record<Sortowanie, string> = {
  najnowsze: 'Najnowsze',
  cena_asc: 'Cena: od najniższej',
  cena_desc: 'Cena: od najwyższej',
  dni_asc: 'Długość pobytu: rosnąco',
  dni_desc: 'Długość pobytu: malejąco',
  termin_od_asc: 'Najbliższy termin',
}
const SORTOWANIE_OPCJE = Object.entries(SORTOWANIE_ETYKIETY) as [Sortowanie, string][]

export function SearchFilters({ filtry, miejscowosci, onZmiana, onWyczysc }: Props) {
  const aktywneFiltry =
    Object.keys(filtry).filter((k) => filtry[k as keyof FiltryWyszukiwania] !== undefined).length > 0

  return (
    <form className="filtry" onSubmit={(e) => e.preventDefault()} aria-label="Wyszukiwarka pobytów">
      <div className="filtry__pole filtry__pole--szeroka">
        <label htmlFor="q">Szukaj</label>
        <input
          id="q"
          type="search"
          placeholder="Ośrodek, miejscowość, nazwa pakietu…"
          value={filtry.q ?? ''}
          onChange={(e) => onZmiana({ ...filtry, q: e.target.value || undefined })}
        />
      </div>

      <div className="filtry__pole">
        <label htmlFor="miejscowosc">Miejscowość</label>
        <select
          id="miejscowosc"
          value={filtry.miejscowosc ?? ''}
          onChange={(e) => onZmiana({ ...filtry, miejscowosc: e.target.value || undefined })}
        >
          <option value="">Wszystkie</option>
          {miejscowosci.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      <div className="filtry__pole">
        <label htmlFor="profil">Profil leczniczy</label>
        <select
          id="profil"
          value={filtry.profil ?? ''}
          onChange={(e) =>
            onZmiana({ ...filtry, profil: (e.target.value || undefined) as ProfilLeczniczy | undefined })
          }
        >
          <option value="">Wszystkie</option>
          {PROFILE_OPCJE.map(([wartosc, etykieta]) => (
            <option key={wartosc} value={wartosc}>
              {etykieta}
            </option>
          ))}
        </select>
      </div>

      <div className="filtry__pole">
        <label htmlFor="wyzywienie">Wyżywienie</label>
        <select
          id="wyzywienie"
          value={filtry.wyzywienie ?? ''}
          onChange={(e) =>
            onZmiana({ ...filtry, wyzywienie: (e.target.value || undefined) as Wyzywienie | undefined })
          }
        >
          <option value="">Dowolne</option>
          {WYZYWIENIE_OPCJE.map(([wartosc, etykieta]) => (
            <option key={wartosc} value={wartosc}>
              {etykieta}
            </option>
          ))}
        </select>
      </div>

      <div className="filtry__pole">
        <label htmlFor="cena_max">Cena maks. (PLN)</label>
        <input
          id="cena_max"
          type="number"
          min={0}
          inputMode="numeric"
          placeholder="np. 3000"
          value={filtry.cena_max ?? ''}
          onChange={(e) =>
            onZmiana({ ...filtry, cena_max: e.target.value ? Number(e.target.value) : undefined })
          }
        />
      </div>

      <div className="filtry__pole">
        <label htmlFor="terminOd">Termin od</label>
        <input
          id="terminOd"
          type="date"
          value={filtry.termin_od ?? ''}
          onChange={(e) => onZmiana({ ...filtry, termin_od: e.target.value || undefined })}
        />
      </div>

      <div className="filtry__pole">
        <label htmlFor="sortuj">Sortuj</label>
        <select
          id="sortuj"
          value={filtry.sortuj ?? 'najnowsze'}
          onChange={(e) => onZmiana({ ...filtry, sortuj: (e.target.value || undefined) as Sortowanie | undefined })}
        >
          {SORTOWANIE_OPCJE.map(([wartosc, etykieta]) => (
            <option key={wartosc} value={wartosc}>
              {etykieta}
            </option>
          ))}
        </select>
      </div>

      <div className="filtry__pole filtry__pole--checkbox">
        <label htmlFor="tylkoDostepne">
          <input
            id="tylkoDostepne"
            type="checkbox"
            checked={filtry.tylko_dostepne ?? false}
            onChange={(e) => onZmiana({ ...filtry, tylko_dostepne: e.target.checked || undefined })}
          />
          Tylko dostępne
        </label>
      </div>

      {aktywneFiltry && (
        <button type="button" className="filtry__wyczysc" onClick={onWyczysc}>
          Wyczyść filtry
        </button>
      )}
    </form>
  )
}
