import { defineStore } from 'pinia'
import { computed, ref, watchEffect } from 'vue'

import {
  applyTheme,
  resolveTheme,
  THEME_STORAGE_KEY,
  type ResolvedTheme,
  type ThemePreference,
} from '@/design/theme'

function readStored(): ThemePreference | null {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY)
    return value === 'light' || value === 'dark' || value === 'system' ? value : null
  } catch {
    return null
  }
}

/**
 * Theme of the interface. The source of truth is the `theme` preference (server); it is cached
 * in localStorage so index.html can apply it before the first paint.
 */
export const useThemeStore = defineStore('theme', () => {
  const preference = ref<ThemePreference>(readStored() ?? 'system')
  const media =
    typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
  const prefersDark = ref(media?.matches ?? false)
  media?.addEventListener('change', (event) => (prefersDark.value = event.matches))

  const resolved = computed<ResolvedTheme>(() => resolveTheme(preference.value, prefersDark.value))

  watchEffect(() => {
    applyTheme(resolved.value)
    try {
      localStorage.setItem(THEME_STORAGE_KEY, preference.value)
    } catch {
      // Storage unavailable (private mode): the preference still comes from the server.
    }
  })

  function set(next: ThemePreference) {
    preference.value = next
  }

  return { preference, resolved, set }
})
