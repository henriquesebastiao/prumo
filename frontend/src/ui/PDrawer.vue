<script setup lang="ts">
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'

const props = defineProps<{
  title: string
  /** Selector of the element focused when it opens (default: the first focusable). */
  initialFocus?: string
}>()
const open = defineModel<boolean>('open', { default: false })

function onOpenAutoFocus(event: Event) {
  if (!props.initialFocus) return
  event.preventDefault()
  requestAnimationFrame(() =>
    document.querySelector<HTMLElement>(`.p-drawer ${props.initialFocus}`)?.focus(),
  )
}
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="p-drawer__overlay" />
      <DialogContent class="p-drawer" @open-auto-focus="onOpenAutoFocus">
        <span class="p-drawer__grip" aria-hidden="true" />
        <DialogTitle class="p-drawer__title">{{ title }}</DialogTitle>
        <slot />
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style>
/* Not scoped: the content is teleported by Reka, which does not forward the scope id. */
.p-drawer__overlay {
  position: fixed;
  z-index: 40;
  inset: 0;
  background: var(--color-scrim);
}

.p-drawer {
  position: fixed;
  z-index: 41;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  max-height: 85dvh;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4) var(--space-6);
  overflow: auto;
  border-radius: var(--radius-2xl) var(--radius-2xl) 0 0;
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-lg);
}

.p-drawer__grip {
  width: 36px;
  height: 4px;
  margin: 0 auto var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
}

.p-drawer__title {
  padding: 0 var(--space-3);
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
}
</style>
