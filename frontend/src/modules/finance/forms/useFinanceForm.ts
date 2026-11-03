import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { isApiError } from '@/lib/api/errors'
import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'

/** Field errors and the general failure of a finance form, from an API error. */
export function useFormErrors() {
  const { t, te } = useI18n()
  const errors = ref<FieldErrors>({})
  const failure = ref<string | null>(null)

  function clear() {
    errors.value = {}
    failure.value = null
  }

  /** `finance.invalid_combination` lists the missing fields: they are shown on the fields. */
  function capture(error: unknown) {
    clear()
    if (isApiError(error) && error.code === 'finance.invalid_combination') {
      const details = error.details as { missing?: string[] }
      errors.value = Object.fromEntries(
        (details.missing ?? []).map((field) => [field, t('fieldErrors.missing')]),
      )
      if (Object.keys(errors.value).length > 0) return
    }
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
  }

  return { errors, failure, capture, clear }
}
