<script setup lang="ts" generic="V extends string">
/** Single choice among pill chips with an icon (categories of a transaction). */
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import type { Option, Tone } from './types'

withDefaults(
  defineProps<{
    options: (Option<V> & { icon?: IconName })[]
    label: string
    /** Color of the icons. */
    tone?: Tone
  }>(),
  { tone: 'neutral' },
)
const model = defineModel<V | ''>({ required: true })
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="p-chip-choice"
    :aria-label="label"
    :data-tone="tone"
    loop
    @update:model-value="(value) => (model = value as V)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      class="p-chip-choice__item"
    >
      <PIcon v-if="option.icon" :name="option.icon" size="sm" class="p-chip-choice__icon" />
      {{ option.label }}
    </RadioGroupItem>
    <slot />
  </RadioGroupRoot>
</template>

<style scoped>
.p-chip-choice {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.p-chip-choice__item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: var(--control-height);
  padding: 0 var(--space-4) 0 var(--space-3-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  cursor: pointer;
}

.p-chip-choice__item:hover {
  background: var(--color-surface-inset);
}

.p-chip-choice__item[data-state='checked'] {
  border-color: var(--color-text);
  box-shadow: var(--shadow-selected-inset);
}

.p-chip-choice__item:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.p-chip-choice__icon {
  color: var(--tone);
}
</style>
