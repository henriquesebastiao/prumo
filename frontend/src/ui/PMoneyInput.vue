<script setup lang="ts">
import { computed } from 'vue'

import { moneyParts } from '@/lib/format'

import PNumberInput from './PNumberInput.vue'

withDefaults(
  defineProps<{
    placeholder?: string
    invalid?: boolean
    disabled?: boolean
    calculated?: boolean
    id?: string
  }>(),
  { placeholder: undefined, id: undefined },
)

/** Value in cents, as the API expects. */
const cents = defineModel<number | null>({ default: null })
const symbol = computed(() => moneyParts(0).symbol)
const amount = computed({
  get: () => (cents.value === null ? null : cents.value / 100),
  set: (value: number | null) => {
    cents.value = value === null ? null : Math.round(value * 100)
  },
})
</script>

<template>
  <PNumberInput
    :id="id"
    v-model="amount"
    :decimals="2"
    :prefix="symbol"
    :placeholder="placeholder"
    :invalid="invalid"
    :disabled="disabled"
    :calculated="calculated"
    align="end"
  />
</template>
