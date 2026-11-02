<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'

const props = withDefaults(
  defineProps<{
    icon: IconName
    /** Accessible name (required: the button has no visible text). */
    label: string
    variant?: 'outline' | 'ghost' | 'tonal' | 'primary'
    size?: 'sm' | 'md'
    iconSize?: 'sm' | 'md'
    disabled?: boolean
    type?: 'button' | 'submit'
    to?: RouteLocationRaw
  }>(),
  { variant: 'ghost', size: 'md', iconSize: 'md', type: 'button', to: undefined },
)

const attrs = computed(() =>
  props.to ? { to: props.to } : { type: props.type, disabled: props.disabled },
)
</script>

<template>
  <component
    :is="to ? RouterLink : 'button'"
    v-bind="attrs"
    class="p-icon-button"
    :class="[`p-icon-button--${variant}`, `p-icon-button--${size}`]"
    :aria-label="label"
    :title="label"
  >
    <PIcon :name="icon" :size="iconSize" />
  </component>
</template>

<style scoped>
.p-icon-button {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.p-icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.p-icon-button--sm {
  width: var(--control-height-sm);
  height: var(--control-height-sm);
}

.p-icon-button--ghost:hover:not(:disabled) {
  background: var(--color-fill);
}

.p-icon-button--outline {
  border-color: var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}

.p-icon-button--outline:hover:not(:disabled) {
  background: var(--color-surface-inset);
}

.p-icon-button--tonal {
  background: var(--color-fill);
  color: var(--color-text);
}

.p-icon-button--primary {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}
</style>
