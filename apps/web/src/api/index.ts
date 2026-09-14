import { createHttpOfertyApi } from './httpApi'
import { mockOfertyApi } from './mockApi'
import type { OfertyApi } from './types'

// Ustaw VITE_API_BASE_URL (np. w apps/web/.env.local), aby przełączyć się
// z danych mockowych na prawdziwy backend (docs/api/specyfikacja.md).
const baseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined

export const ofertyApi: OfertyApi = baseUrl ? createHttpOfertyApi(baseUrl) : mockOfertyApi

export type { FiltryWyszukiwania, OfertyApi, Sortowanie } from './types'
export { BladApi } from './types'
