<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'
import { useI18n } from 'vue-i18n'

import type { IconName } from './icons'
import PIconButton from './PIconButton.vue'
import PTile from './PTile.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    title: string
    description?: string
    size?: 's' | 'm' | 'l'
    icon?: IconName
    tone?: Tone
    closable?: boolean
    /** `row`: icon, title and close button in one line. `stacked`: icon above (confirmations). */
    layout?: 'row' | 'stacked'
    /** Static rendering, without overlay or focus trap (used by the /dev/ui showcase). */
    inline?: boolean
  }>(),
  {
    description: undefined,
    size: 'm',
    icon: undefined,
    tone: 'neutral',
    closable: true,
    layout: 'row',
  },
)

const open = defineModel<boolean>('open', { default: false })

const FIELDS =
  'input:not([readonly]), textarea, select, [role="radio"][data-state="checked"], button'

/** Forms open with the first field focused instead of the close button. */
function focusFirstField(event: Event) {
  const content = event.currentTarget instanceof HTMLElement ? event.currentTarget : null
  const field = content?.querySelector<HTMLElement>(`.p-dialog__body :is(${FIELDS})`)
  if (!field) return
  event.preventDefault()
  requestAnimationFrame(() => field.focus())
}
const { t } = useI18n()
</script>

<template>
  <div
    v-if="inline"
    class="p-dialog"
    :class="`p-dialog--${size}`"
    role="dialog"
    :aria-label="title"
  >
    <header
      class="p-dialog__header"
      :class="{ 'p-dialog__header--stacked': icon && layout === 'stacked' }"
    >
      <PTile v-if="icon" :icon="icon" :tone="tone" />
      <h2 class="p-dialog__title">{{ title }}</h2>
      <PIconButton
        v-if="closable && layout === 'row'"
        icon="close"
        icon-size="sm"
        :label="t('ui.close')"
      />
    </header>
    <div class="p-dialog__body">
      <p v-if="description" class="p-dialog__description">{{ description }}</p>
      <slot />
    </div>
    <footer v-if="$slots.footer" class="p-dialog__footer"><slot name="footer" /></footer>
  </div>
  <DialogRoot v-else v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="p-dialog__overlay" />
      <DialogContent
        class="p-dialog p-dialog--modal"
        :class="`p-dialog--${size}`"
        @open-auto-focus="focusFirstField"
      >
        <header
          class="p-dialog__header"
          :class="{ 'p-dialog__header--stacked': icon && layout === 'stacked' }"
        >
          <PTile v-if="icon" :icon="icon" :tone="tone" />
          <div class="p-dialog__titles">
            <DialogTitle class="p-dialog__title">{{ title }}</DialogTitle>
            <DialogDescription v-if="description && layout === 'row'" class="p-dialog__subtitle">{{
              description
            }}</DialogDescription>
          </div>
          <DialogClose v-if="closable && layout === 'row'" as-child>
            <PIconButton icon="close" icon-size="sm" :label="t('ui.close')" />
          </DialogClose>
        </header>
        <div class="p-dialog__body">
          <DialogDescription
            v-if="description && layout === 'stacked'"
            class="p-dialog__description"
            >{{ description }}</DialogDescription
          >
          <slot />
        </div>
        <footer v-if="$slots.footer" class="p-dialog__footer"><slot name="footer" /></footer>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style>
/* Not scoped: the content is teleported by Reka, which does not forward the scope id. */
.p-dialog__overlay {
  position: fixed;
  z-index: 40;
  inset: 0;
  background: var(--color-scrim);
}

.p-dialog {
  display: flex;
  width: 100%;
  max-width: 640px;
  flex-direction: column;
  border-radius: var(--radius-2xl);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-lg);
}

.p-dialog--modal {
  position: fixed;
  z-index: 41;
  top: 56px;
  left: 50%;
  max-height: calc(100dvh - 112px);
  overflow: auto;
  transform: translateX(-50%);
  width: calc(100% - 48px);
}

.p-dialog--s {
  max-width: 440px;
}

.p-dialog--l {
  max-width: 760px;
}

.p-dialog__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4-5) var(--space-4) 0 var(--space-6);
}

.p-dialog__header--stacked {
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-5);
  padding: var(--space-6) var(--space-6) 0;
}

.p-dialog__titles {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: var(--space-0-5);
}

.p-dialog__subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.p-dialog__title {
  flex: 1;
  min-width: 0;
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-snug);
}

.p-dialog__header--stacked .p-dialog__title {
  font-size: var(--text-2xl);
  letter-spacing: var(--tracking-snug);
}

.p-dialog__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
}

.p-dialog__description {
  color: var(--color-text-secondary);
  text-wrap: pretty;
}

.p-dialog__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6) var(--space-5);
  border-top: 1px solid var(--color-divider);
}

/* Phones: full-screen sheet with a fixed footer. */
@media (width < 600px) {
  .p-dialog--modal {
    top: 0;
    left: 0;
    width: 100%;
    max-width: none;
    height: 100dvh;
    max-height: none;
    border-radius: 0;
    transform: none;
  }

  .p-dialog--modal .p-dialog__body {
    flex: 1;
  }

  .p-dialog--modal .p-dialog__footer {
    position: sticky;
    bottom: 0;
    background: var(--color-surface-raised);
  }

  .p-dialog--modal .p-dialog__footer > * {
    flex: 1;
  }
}
</style>
