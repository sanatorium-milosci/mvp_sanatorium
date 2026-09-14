import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

describe('Przejście z listy do szczegółów oferty', () => {
  it('otwiera szczegóły po kliknięciu karty i pozwala wrócić do wyników', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())

    await user.click(screen.getByText('Pobyt lecznico-wypoczynkowy 7 dni'))

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Uzdrowisko Ustroń — Sanatorium Równica' })).toBeInTheDocument(),
    )
    expect(screen.getByText('Zobacz stronę ośrodka ↗')).toBeInTheDocument()
    expect(screen.getByText('Przejdź do rezerwacji ↗')).toBeInTheDocument()

    await user.click(screen.getByText('← Wróć do wyników'))

    await waitFor(() => expect(screen.getByText(/Znaleziono 6 ofert/)).toBeInTheDocument())
  })

  it('pokazuje komunikat dla nieistniejącego id oferty', async () => {
    render(
      <MemoryRouter initialEntries={['/oferta/nie-istnieje']}>
        <App />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Nie znaleziono oferty.')).toBeInTheDocument())
  })
})
