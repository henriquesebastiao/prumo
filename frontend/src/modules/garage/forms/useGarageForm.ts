import { computed, ref, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { isApiError } from '@/lib/api/errors'
import { errorMessage } from '@/lib/errors'
import { dateShort, isoToZoned, km as formatKm } from '@/lib/format'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'

import { useVehicles, type Vehicle } from '../api'
import { lastUsedVehicle } from '../helpers'

/** Field errors and the general failure of a garage form, from an API error. */
export function useFormErrors() {
  const { t, te } = useI18n()
  const errors = ref<FieldErrors>({})
  const failure = ref<string | null>(null)

  function clear() {
    errors.value = {}
    failure.value = null
  }

  /** G3: the odometer conflict is shown on the km field with the conflicting reading. */
  function capture(error: unknown, kmField = 'km') {
    clear()
    if (isApiError(error) && error.code === 'garage.odometer_inconsistent') {
      const details = error.details as { conflict?: string; km?: number; recorded_at?: string }
      errors.value = {
        [kmField]: t(details.conflict === 'next' ? 'garage.form.kmHigher' : 'garage.form.kmLower', {
          km: formatKm(details.km ?? 0),
          date: details.recorded_at ? dateShort(details.recorded_at) : '',
        }),
      }
      return
    }
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
  }

  return { errors, failure, capture, clear }
}

/** Vehicles for a form, with the selected one: the given id, or the one used last (design). */
export function useVehicleChoice(open: Ref<boolean>, vehicleId: () => string | undefined) {
  const vehicles = useVehicles()
  const selectedId = ref<string>('')
  const list = computed<Vehicle[]>(() => vehicles.data.value ?? [])
  const selected = computed(() => list.value.find((v) => v.id === selectedId.value))

  function pick() {
    selectedId.value = vehicleId() ?? lastUsedVehicle(list.value)?.id ?? ''
  }
  watch(open, (value) => value && pick(), { immediate: true })
  watch(list, () => {
    if (!selected.value) pick()
  })

  return { vehicles: list, selectedId, selected, loading: vehicles.isPending }
}

/** Current day and time in the user's time zone, to prefill date and time fields. */
export function nowFields(): { day: string; time: string } {
  return isoToZoned(new Date())
}
