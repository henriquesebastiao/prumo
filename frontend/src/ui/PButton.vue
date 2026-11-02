<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import PSpinner from './PSpinner.vue'
import type { Tone } from './types'

const props = withDefaults(
  defineProps<{
    /** `chip`: quick action. `dashed`: large placeholder to add an item ("Adicionar veículo"). */
    variant?: 'primary' | 'outline' | 'tonal' | 'ghost' | 'danger' | 'chip' | 'dashed'
    size?: 'md' | 'lg'
    icon?: IconName
    iconTone?: Tone
    iconRight?: IconName
    block?: boolean
    loading?: boolean
    disabled?: boolean
    type?: 'button' | 'submit' | 'reset'
    to?: RouteLocationRaw
  }>(),
  {
    variant: 'outline',
    size: 'md',
    icon: undefined,
    iconTone: undefined,
    iconRight: undefined,
    type: 'button',
    to: undefined,
  },
)

const attrs = computed(() =>
  props.to
    ? { to: props.to, 'aria-disabled': props.disabled ? 'true' : undefined }
    : { type: props.type, disabled: props.disabled || props.loading },
)
</script>

<template>
  <component
    :is="to ? RouterLink : 'button'"
    v-bind="attrs"
    class="p-button"
    :class="[`p-button--${variant}`, `p-button--${size}`, { 'p-button--block': block }]"
    :aria-busy="loading || undefined"
  >
    <PSpinner v-if="loading" size="sm" />
    <PIcon v-else-if="icon" :name="icon" :data-tone="iconTone" />
    <slot />
    <PIcon v-if="iconRight" :name="iconRight" size="sm" />
  </component>
</template>

<style scoped>
.p-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: var(--control-height);
  padding: 0 var(--space-4-5);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  text-decoration: none;
  white-space: nowrap;
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.p-button:disabled,
.p-button[aria-disabled='true'] {
  cursor: not-allowed;
  opacity: 0.5;
}

.p-button--primary {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.p-button--outline {
  border-color: var(--color-border);
  background: var(--color-surface);
}

.p-button--outline:hover:not(:disabled) {
  background: var(--color-surface-inset);
}

.p-button--tonal {
  background: var(--color-fill);
}

.p-button--ghost {
  color: var(--color-text-secondary);
}

.p-button--ghost:hover:not(:disabled) {
  background: var(--color-fill);
}

.p-button--danger {
  background: var(--color-danger);
  color: var(--color-on-danger);
}

.p-button--chip {
  padding: 0 var(--space-4) 0 var(--space-3);
  border-color: var(--color-border);
  background: var(--color-surface);
  font-weight: var(--weight-semibold);
}

.p-button--chip:hover:not(:disabled) {
  background: var(--color-surface-inset);
}

.p-button--dashed {
  width: 100%;
  height: 72px;
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius-xl);
  font-size: var(--text-lg);
}

.p-button--dashed:hover:not(:disabled) {
  background: var(--color-surface-inset);
}

.p-button--lg {
  height: var(--control-height-lg);
  padding: 0 var(--space-6);
  font-size: var(--text-lg);
}

.p-button--block {
  width: 100%;
}
</style>
