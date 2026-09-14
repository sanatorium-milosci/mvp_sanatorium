import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { SearchPage } from './SearchPage'

function renderSearchPage() {
  return render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>,
  )
}

describe('SearchPage', () => {
  it('pokazuje stan ładowania, a następnie listę wszystkich ofert', async () => {
    renderSearchPage()

    expect(screen.getByText('Szukamy ofert…')).toBeInTheDocument()

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())
    expect(screen.getAllByRole('listitem')).toHaveLength(6)
  })

  it('filtruje oferty po frazie wyszukiwania', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())

    await user.type(screen.getByLabelText('Szukaj'), 'Kołobrzeg')

    await waitFor(() => expect(screen.getByText(/Znaleziono 2 ofert/)).toBeInTheDocument())
    expect(screen.getAllByText('Sanatorium Perła Bałtyku')).toHaveLength(2)
  })

  it('pokazuje komunikat o braku wyników dla nieistniejącej frazy', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())

    await user.type(screen.getByLabelText('Szukaj'), 'nie-ma-takiego-osrodka-xyz')

    await waitFor(() =>
      expect(screen.getByText('Brak ofert spełniających podane kryteria.')).toBeInTheDocument(),
    )
  })

  it('filtruje oferty po miejscowości i pokazuje przycisk czyszczenia filtrów', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText('Miejscowość'), 'Ustroń')

    await waitFor(() => expect(screen.getByText(/Znaleziono 2 ofert/)).toBeInTheDocument())

    const wyczyscButton = screen.getByRole('button', { name: 'Wyczyść filtry' })
    await user.click(wyczyscButton)

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())
  })

  it('domyślnie ukrywa zakończone terminy i pokazuje je po zaznaczeniu checkboxa', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())
    expect(screen.queryByText('Turnus letni 7 dni (zakończony)')).not.toBeInTheDocument()

    await user.click(screen.getByLabelText('Pokaż też zakończone terminy'))

    await waitFor(() => expect(screen.getByText(/Znaleziono 7 ofert/)).toBeInTheDocument())
    expect(screen.getByText('Turnus letni 7 dni (zakończony)')).toBeInTheDocument()
  })
})
