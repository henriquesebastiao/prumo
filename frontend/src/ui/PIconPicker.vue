<script setup lang="ts" generic="V extends string">
/** Single choice among icons (account and category icons). */
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    label: string
    options: { value: V; icon: IconName; label: string }[]
    /** Color of the selected icon. */
    tone?: Tone
  }>(),
  { tone: 'neutral' },
)
const model = defineModel<V>({ required: true })
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="p-icon-picker"
    :aria-label="label"
    :data-tone="tone"
    loop
    @update:model-value="(value) => (model = value as V)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      :aria-label="option.label"
      :title="option.label"
      class="p-icon-picker__item"
    >
      <PIcon :name="option.icon" />
    </RadioGroupItem>
  </RadioGroupRoot>
</template>

<style scoped>
.p-icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.p-icon-picker__item {
  display: inline-grid;
  width: var(--control-height);
  height: var(--control-height);
  place-items: center;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  background: var(--color-fill);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.p-icon-picker__item:hover {
  color: var(--color-text);
}

.p-icon-picker__item[data-state='checked'] {
  border-color: var(--tone);
  background: var(--tone-container);
  color: var(--tone-on-container);
}

.p-icon-picker__item:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
</style>
