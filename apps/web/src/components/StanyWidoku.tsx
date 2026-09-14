export function StanLadowania() {
  return (
    <div className="stan-widoku" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>Szukamy ofert…</p>
    </div>
  )
}

export function StanBrakWynikow() {
  return (
    <div className="stan-widoku" role="status">
      <p>Brak ofert spełniających podane kryteria.</p>
      <p className="stan-widoku__podpowiedz">Spróbuj zmienić lub wyczyścić filtry.</p>
    </div>
  )
}

interface StanBleduProps {
  komunikat?: string
  onPonow?: () => void
}

export function StanBledu({ komunikat, onPonow }: StanBleduProps) {
  return (
    <div className="stan-widoku stan-widoku--blad" role="alert">
      <p>Nie udało się pobrać ofert.</p>
      {komunikat && <p className="stan-widoku__podpowiedz">{komunikat}</p>}
      {onPonow && (
        <button type="button" onClick={onPonow}>
          Spróbuj ponownie
        </button>
      )}
    </div>
  )
}
