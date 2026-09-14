import { createHttpOfertyApi } from './httpApi'
import { mockOfertyApi } from './mockApi'
import type { OfertyApi } from './types'

// Produkcyjny build korzysta z API pod tym samym adresem co Caddy.
// VITE_API_BASE_URL pozwala wskazać osobny backend, także w development.
// Dane demonstracyjne pozostają domyślne wyłącznie poza produkcją.
const baseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined

export const ofertyApi: OfertyApi = baseUrl
  ? createHttpOfertyApi(baseUrl)
  : import.meta.env.PROD
    ? createHttpOfertyApi(window.location.origin)
    : mockOfertyApi

export type { FiltryWyszukiwania, OfertyApi, Sortowanie } from './types'
export { BladApi } from './types'
