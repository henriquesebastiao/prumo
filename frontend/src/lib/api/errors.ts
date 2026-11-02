import type { components } from './schema'

type ErrorBody = components['schemas']['ErrorBody']
export type ApiFieldError = components['schemas']['ErrorField']

/**
 * Every failed request ends as an ApiError. `code` is the stable code from the API
 * (`auth.invalid_credentials`, `validation_error`, `garage.odometer_inconsistent`…) and is what
 * the interface translates; `message` is English, for debugging only.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>
  readonly fields: ApiFieldError[]

  constructor(status: number, body: Partial<ErrorBody>) {
    super(body.message ?? `HTTP ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code ?? 'http_error'
    this.details = body.details ?? {}
    this.fields = body.fields ?? []
  }

  /** Field errors keyed by path (`items.0.unit_price_cents`), for form mapping. */
  fieldErrors(): Record<string, ApiFieldError> {
    return Object.fromEntries(this.fields.map((field) => [field.path, field]))
  }

  static network(cause: unknown): ApiError {
    const error = new ApiError(0, { code: 'network_error', message: 'Network request failed.' })
    error.cause = cause
    return error
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}

/** Reads `{ error: {...} }` from an unknown error payload. */
export function toApiError(status: number, payload: unknown): ApiError {
  if (payload && typeof payload === 'object' && 'error' in payload) {
    const body = (payload as { error: unknown }).error
    if (body && typeof body === 'object') return new ApiError(status, body as Partial<ErrorBody>)
  }
  return new ApiError(status, {})
}
