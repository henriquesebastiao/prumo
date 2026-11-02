import { onBeforeUnmount, ref } from 'vue'

/** Reactive `matchMedia`. */
export function useMediaQuery(query: string) {
  const media = typeof window !== 'undefined' ? window.matchMedia(query) : null
  const matches = ref(media?.matches ?? false)
  const update = (event: MediaQueryListEvent) => (matches.value = event.matches)
  media?.addEventListener('change', update)
  onBeforeUnmount(() => media?.removeEventListener('change', update))
  return matches
}

/** True when focus is in a field where typing must not trigger shortcuts. */
export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return (
    target.isContentEditable ||
    ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) ||
    target.closest('[role="dialog"], [role="menu"], [role="listbox"]') !== null
  )
}
