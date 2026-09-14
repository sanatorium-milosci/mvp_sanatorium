import { afterEach, describe, expect, it, vi } from 'vitest'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.resetModules()
})

describe('wybór API', () => {
  it('produkcyjny build bez konfiguracji pobiera prawdziwe dane z tego samego hosta', async () => {
    vi.stubEnv('PROD', true)
    vi.stubEnv('VITE_API_BASE_URL', '')
    const dane = { elementy: [], stronicowanie: { razem: 0 } }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => dane })
    vi.stubGlobal('fetch', fetchMock)
    const { ofertyApi } = await import('./index')

    expect(await ofertyApi.szukaj({ pokaz_przeszle: false })).toEqual(dane)
    expect(fetchMock).toHaveBeenCalledWith(
      `${window.location.origin}/api/v1/oferty?pokaz_przeszle=false`,
    )
  })

  it('respektuje jawnie wskazany backend', async () => {
    vi.stubEnv('PROD', true)
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com')
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    const { ofertyApi } = await import('./index')

    await ofertyApi.pobierzFiltry()
    expect(fetchMock).toHaveBeenCalledWith('https://api.example.com/api/v1/filtry')
  })

  it('nie zastępuje błędu produkcyjnego API przykładowymi ofertami', async () => {
    vi.stubEnv('PROD', true)
    vi.stubEnv('VITE_API_BASE_URL', '')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { ofertyApi } = await import('./index')

    await expect(ofertyApi.szukaj({})).rejects.toThrow('Brak połączenia z serwerem')
  })
})
