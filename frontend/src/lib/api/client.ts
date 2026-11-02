import createClient, { type Middleware } from 'openapi-fetch'

import { ApiError, toApiError } from './errors'
import type { components, paths } from './schema'

export type Schemas = components['schemas']

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

/** The web authenticates with the HttpOnly cookie; mutations must identify the client (CSRF). */
const clientHeader: Middleware = {
  onRequest({ request }) {
    if (MUTATING_METHODS.has(request.method)) request.headers.set('X-Prumo-Client', 'web')
    return request
  },
}

type UnauthorizedListener = (error: ApiError) => void
const unauthorizedListeners = new Set<UnauthorizedListener>()

/** Called when a request answers 401 (session missing or expired). Returns an unsubscribe. */
export function onUnauthorized(listener: UnauthorizedListener): () => void {
  unauthorizedListeners.add(listener)
  return () => unauthorizedListeners.delete(listener)
}

export function createApiClient(fetchImpl?: typeof fetch) {
  const client = createClient<paths>({
    // Same origin as the SPA (nginx in production, Vite's proxy in development).
    baseUrl: globalThis.location?.origin ?? '',
    credentials: 'same-origin',
    ...(fetchImpl ? { fetch: fetchImpl } : {}),
  })
  client.use(clientHeader)
  return client
}

export const api = createApiClient()

type Result<T> =
  | { data: T; error?: never; response: Response }
  | { data?: never; error: unknown; response: Response }

/**
 * Turns an openapi-fetch result into data or a thrown ApiError (what TanStack Query expects).
 * Network failures become `ApiError` with status 0 and code `network_error`.
 */
export async function unwrap<T>(request: Promise<Result<T>>): Promise<T> {
  let result: Result<T>
  try {
    result = await request
  } catch (cause) {
    throw ApiError.network(cause)
  }
  if (result.error !== undefined || !result.response.ok) {
    const error = toApiError(result.response.status, result.error)
    if (error.status === 401) unauthorizedListeners.forEach((listener) => listener(error))
    throw error
  }
  return result.data as T
}
