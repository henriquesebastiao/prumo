<script setup lang="ts" generic="V extends string">
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import type { Option } from './types'

withDefaults(
  defineProps<{
    options: (Option<V> & { icon?: IconName })[]
    label: string
    block?: boolean
    disabled?: boolean
  }>(),
  {},
)
const model = defineModel<V>({ required: true })
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="p-segmented"
    :class="{ 'p-segmented--block': block }"
    :aria-label="label"
    :disabled="disabled"
    orientation="horizontal"
    loop
    @update:model-value="(value) => (model = value as V)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      class="p-segmented__item"
    >
      <PIcon v-if="option.icon" :name="option.icon" size="sm" />
      {{ option.label }}
    </RadioGroupItem>
  </RadioGroupRoot>
</template>

<style scoped>
.p-segmented {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  padding: var(--space-1);
  border-radius: var(--radius-full);
  background: var(--color-fill);
}

.p-segmented--block {
  display: flex;
}

.p-segmented__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1-5);
  height: var(--control-height-sm);
  padding: 0 var(--space-4);
  border: 0;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
}

.p-segmented--block .p-segmented__item {
  flex: 1;
}

.p-segmented__item[data-state='checked'] {
  background: var(--color-surface);
  color: var(--color-text);
  font-weight: var(--weight-bold);
  box-shadow: var(--shadow-sm);
}
</style>
