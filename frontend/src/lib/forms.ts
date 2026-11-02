import type { ZodError } from 'zod'

import { isApiError } from './api/errors'
import { fieldErrorMessage } from './errors'

interface Translator {
  t: (key: string, values?: Record<string, unknown>) => string
  te: (key: string) => boolean
}

export type FieldErrors = Record<string, string>

/** Errors of a failed request, by field path, translated. */
export function apiFieldErrors(error: unknown, translator: Translator): FieldErrors {
  if (!isApiError(error)) return {}
  return Object.fromEntries(
    error.fields.map((field) => [field.path, fieldErrorMessage(field.code, translator)]),
  )
}

/** Errors of a Zod validation, by field path. Messages are written already translated. */
export function zodFieldErrors(error: ZodError): FieldErrors {
  const errors: FieldErrors = {}
  for (const issue of error.issues) {
    const path = issue.path.join('.')
    errors[path] ??= issue.message
  }
  return errors
}
