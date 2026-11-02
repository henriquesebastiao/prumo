<script setup lang="ts" generic="V extends string">
import {
  SelectContent,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport,
} from 'reka-ui'

import { useField } from './field'
import PIcon from './PIcon.vue'
import type { Option } from './types'

const props = withDefaults(
  defineProps<{
    options: Option<V>[]
    placeholder?: string
    invalid?: boolean
    disabled?: boolean
    id?: string
    /** Render the list in place (used by the /dev/ui showcase). */
    portal?: boolean
  }>(),
  { placeholder: undefined, id: undefined, portal: true },
)

const model = defineModel<V>({ required: true })
const field = useField(props)
</script>

<template>
  <SelectRoot
    :model-value="model"
    :disabled="disabled"
    @update:model-value="(value) => (model = value as V)"
  >
    <SelectTrigger
      :id="field.id.value"
      class="p-control p-select"
      :class="{ 'p-control--invalid': field.invalid.value, 'p-control--disabled': disabled }"
      :aria-invalid="field.invalid.value || undefined"
      :aria-describedby="field.describedBy.value"
    >
      <SelectValue class="p-select__value" :placeholder="placeholder" />
      <PIcon name="chevron-down" size="sm" class="p-control__icon" />
    </SelectTrigger>
    <SelectPortal :disabled="!portal">
      <SelectContent class="p-options" position="popper" :side-offset="6">
        <SelectViewport>
          <SelectItem
            v-for="option in options"
            :key="option.value"
            :value="option.value"
            class="p-options__item"
          >
            <SelectItemText class="p-options__text">{{ option.label }}</SelectItemText>
            <SelectItemIndicator><PIcon name="check" size="sm" /></SelectItemIndicator>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>

<style src="./control.css"></style>

<style scoped>
.p-select {
  justify-content: space-between;
  font-size: var(--text-base);
  text-align: left;
}

.p-select__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.p-select__value[data-placeholder] {
  color: var(--color-text-muted);
}
</style>
