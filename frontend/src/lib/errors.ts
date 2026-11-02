import { isApiError } from './api/errors'

interface Translator {
  t: (key: string, values?: Record<string, unknown>) => string
  te: (key: string) => boolean
}

/**
 * Translated message for an error. API codes (`auth.invalid_credentials`) map to
 * `errors.<code>` in the locale files; unknown codes fall back to a generic message.
 */
export function errorMessage(error: unknown, { t, te }: Translator): string {
  if (isApiError(error)) {
    const key = `errors.${error.code}`
    if (te(key)) return t(key, error.details)
    if (error.status >= 500) return t('errors.internal_error')
  }
  return t('errors.unknown')
}

/** Translated message for one field error, from its Pydantic or domain code. */
export function fieldErrorMessage(code: string, { t, te }: Translator): string {
  const key = `fieldErrors.${code}`
  return te(key) ? t(key) : t('fieldErrors.invalid')
}
