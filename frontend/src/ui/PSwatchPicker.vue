<script setup lang="ts" generic="V extends string">
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

defineProps<{
  label: string
  /** `color` is a CSS color token, such as `var(--color-swatch-blue)`. */
  options: { value: V; label: string; color: string }[]
}>()
const model = defineModel<V>({ required: true })
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="p-swatches"
    :aria-label="label"
    loop
    @update:model-value="(value) => (model = value as V)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      :aria-label="option.label"
      class="p-swatches__item"
      :style="{ backgroundColor: option.color }"
    />
  </RadioGroupRoot>
</template>

<style scoped>
.p-swatches {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2-5);
}

.p-swatches__item {
  flex: none;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: 50%;
}

.p-swatches__item[data-state='checked'] {
  box-shadow: var(--shadow-selected);
}
</style>
