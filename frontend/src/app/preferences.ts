import { watch } from 'vue'

import { configureFormat } from '@/lib/format'
import { usePreferences } from '@/system/api'

import { useThemeStore } from './stores/theme'

/** Applies the server preferences to the interface: theme and formatting (locale, zone, money). */
export function useApplyPreferences() {
  const preferences = usePreferences()
  const theme = useThemeStore()
  watch(
    () => preferences.data.value,
    (value) => {
      if (!value) return
      theme.set(value.theme)
      configureFormat({ locale: value.locale, timeZone: value.timezone, currency: value.currency })
    },
    { immediate: true },
  )
  return preferences
}
