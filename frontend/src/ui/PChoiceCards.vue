<script setup lang="ts" generic="V extends string">
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import PIcon from './PIcon.vue'
import type { Option } from './types'

defineProps<{ options: Option<V>[]; label: string }>()
const model = defineModel<V>({ required: true })
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="p-choices"
    :aria-label="label"
    loop
    @update:model-value="(value) => (model = value as V)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      class="p-choices__item"
    >
      <slot name="preview" :option="option" />
      <span class="p-choices__label">
        <span>
          <b>{{ option.label }}</b>
          <span v-if="option.description" class="p-choices__description">
            · {{ option.description }}</span
          >
        </span>
        <PIcon v-if="model === option.value" name="check" size="sm" />
      </span>
    </RadioGroupItem>
  </RadioGroupRoot>
</template>

<style scoped>
.p-choices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
  gap: var(--space-3);
}

.p-choices__item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 2px solid transparent;
  border-radius: var(--radius-lg);
  background: var(--color-surface-inset);
  color: var(--color-text);
  text-align: left;
}

.p-choices__item[data-state='checked'] {
  border-color: var(--color-focus);
  background: var(--color-surface);
}

.p-choices__label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.p-choices__label b {
  font-weight: var(--weight-bold);
}

.p-choices__description {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}
</style>
