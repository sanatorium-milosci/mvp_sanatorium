import { mockOfertyApi } from './mockApi'
import type { OfertyApi } from './types'

// Jedyne miejsce, w którym trzeba podmienić implementację po publikacji
// prawdziwego API w docs/api/ (backend: Antigravity/Michał).
// Docelowo: import { httpOfertyApi } from './httpApi'
export const ofertyApi: OfertyApi = mockOfertyApi

export type { FiltryWyszukiwania, WynikWyszukiwania, OfertyApi } from './types'
export { BladApi } from './types'
