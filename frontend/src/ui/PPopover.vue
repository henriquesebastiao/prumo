<script setup lang="ts">
import { PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'

const props = withDefaults(
  defineProps<{
    side?: 'top' | 'right' | 'bottom' | 'left'
    align?: 'start' | 'center' | 'end'
    label?: string
    portal?: boolean
    width?: string
    /** Selector of the element focused when it opens (default: the first focusable). */
    initialFocus?: string
  }>(),
  {
    side: 'bottom',
    align: 'start',
    label: undefined,
    portal: true,
    width: '340px',
    initialFocus: undefined,
  },
)
const open = defineModel<boolean>('open', { default: false })

function onOpenAutoFocus(event: Event) {
  if (!props.initialFocus) return
  event.preventDefault()
  const content = event.currentTarget instanceof HTMLElement ? event.currentTarget : null
  requestAnimationFrame(() =>
    (content ?? document).querySelector<HTMLElement>(props.initialFocus!)?.focus(),
  )
}
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child><slot name="trigger" /></PopoverTrigger>
    <PopoverPortal :disabled="!portal">
      <PopoverContent
        class="p-popover"
        :side="side"
        :align="align"
        :side-offset="8"
        :collision-padding="16"
        :aria-label="label"
        :style="{ width }"
        @open-auto-focus="onOpenAutoFocus"
      >
        <slot />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
/* Not scoped: the content is teleported by Reka, which does not forward the scope id. */
.p-popover {
  z-index: 50;
  display: flex;
  max-width: calc(100vw - 32px);
  flex-direction: column;
  gap: var(--space-3-5);
  padding: var(--space-4-5);
  border-radius: var(--radius-menu);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-lg);
}
</style>
