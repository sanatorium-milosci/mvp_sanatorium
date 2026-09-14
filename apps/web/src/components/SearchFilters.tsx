import type { FiltryWyszukiwania } from '../api'
import { PROFILE_LECZNICZE_ETYKIETY, WYZYWIENIE_ETYKIETY, type ProfilLeczniczy, type Wyzywienie } from '../types/oferta'

interface Props {
  filtry: FiltryWyszukiwania
  miejscowosci: string[]
  onZmiana: (filtry: FiltryWyszukiwania) => void
  onWyczysc: () => void
}

const PROFILE_OPCJE = Object.entries(PROFILE_LECZNICZE_ETYKIETY) as [ProfilLeczniczy, string][]
const WYZYWIENIE_OPCJE = Object.entries(WYZYWIENIE_ETYKIETY) as [Wyzywienie, string][]

export function SearchFilters({ filtry, miejscowosci, onZmiana, onWyczysc }: Props) {
  const aktywneFiltry =
    Object.keys(filtry).filter((k) => filtry[k as keyof FiltryWyszukiwania] !== undefined).length > 0

  return (
    <form className="filtry" onSubmit={(e) => e.preventDefault()} aria-label="Wyszukiwarka pobytów">
      <div className="filtry__pole filtry__pole--szeroka">
        <label htmlFor="fraza">Szukaj</label>
        <input
          id="fraza"
          type="search"
          placeholder="Ośrodek, miejscowość, nazwa pakietu…"
          value={filtry.fraza ?? ''}
          onChange={(e) => onZmiana({ ...filtry, fraza: e.target.value || undefined })}
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
        <label htmlFor="cenaMax">Cena maks. (PLN)</label>
        <input
          id="cenaMax"
          type="number"
          min={0}
          inputMode="numeric"
          placeholder="np. 3000"
          value={filtry.cenaMax ?? ''}
          onChange={(e) =>
            onZmiana({ ...filtry, cenaMax: e.target.value ? Number(e.target.value) : undefined })
          }
        />
      </div>

      <div className="filtry__pole">
        <label htmlFor="terminOd">Termin od</label>
        <input
          id="terminOd"
          type="date"
          value={filtry.terminOd ?? ''}
          onChange={(e) => onZmiana({ ...filtry, terminOd: e.target.value || undefined })}
        />
      </div>

      <div className="filtry__pole filtry__pole--checkbox">
        <label htmlFor="tylkoDostepne">
          <input
            id="tylkoDostepne"
            type="checkbox"
            checked={filtry.tylkoDostepne ?? false}
            onChange={(e) => onZmiana({ ...filtry, tylkoDostepne: e.target.checked || undefined })}
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
