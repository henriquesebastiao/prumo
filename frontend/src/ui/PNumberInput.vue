<script setup lang="ts">
import { ref, watch } from 'vue'

import { formatLocaleNumber, parseLocaleNumber } from './number'
import PInput from './PInput.vue'

const props = withDefaults(
  defineProps<{
    decimals?: number
    prefix?: string
    suffix?: string
    placeholder?: string
    invalid?: boolean
    disabled?: boolean
    calculated?: boolean
    align?: 'start' | 'end'
    id?: string
  }>(),
  {
    decimals: 0,
    prefix: undefined,
    suffix: undefined,
    placeholder: undefined,
    align: 'start',
    id: undefined,
  },
)

const model = defineModel<number | null>({ default: null })
const text = ref(formatLocaleNumber(model.value, props.decimals))

watch(model, (value) => {
  if (parseLocaleNumber(text.value) !== value)
    text.value = formatLocaleNumber(value, props.decimals)
})

function onInput(value: string) {
  text.value = value
  const parsed = parseLocaleNumber(value)
  model.value = parsed === null ? null : Number(parsed.toFixed(props.decimals))
}

function onBlur() {
  text.value = formatLocaleNumber(model.value, props.decimals)
}
</script>

<template>
  <PInput
    :id="id"
    :model-value="text"
    :prefix="prefix"
    :suffix="suffix"
    :placeholder="placeholder"
    :invalid="invalid"
    :disabled="disabled"
    :calculated="calculated"
    :align="align"
    :inputmode="decimals === 0 ? 'numeric' : 'decimal'"
    autocomplete="off"
    @update:model-value="onInput"
    @blur="onBlur"
  />
</template>
