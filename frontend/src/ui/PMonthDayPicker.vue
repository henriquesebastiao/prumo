<script setup lang="ts">
/** Days of the month to pick (several), 1 to 31, in rows of seven. */
import type { Tone } from './types'

const props = withDefaults(defineProps<{ label: string; tone?: Tone; disabled?: boolean }>(), {
  tone: 'accent',
  disabled: false,
})
const model = defineModel<number[]>({ default: () => [] })
const days = Array.from({ length: 31 }, (_, index) => index + 1)

function toggle(day: number) {
  if (props.disabled) return
  const set = new Set(model.value)
  if (set.has(day)) set.delete(day)
  else set.add(day)
  model.value = [...set].sort((a, b) => a - b)
}
</script>

<template>
  <div class="p-month-days" role="group" :aria-label="label" :data-tone="tone">
    <button
      v-for="day in days"
      :key="day"
      type="button"
      class="p-month-days__day"
      :class="{ 'p-month-days__day--on': model.includes(day) }"
      :aria-pressed="model.includes(day)"
      :disabled="disabled"
      @click="toggle(day)"
    >
      {{ day }}
    </button>
  </div>
</template>

<style scoped>
.p-month-days {
  display: grid;
  max-width: calc(7 * var(--control-height) + 6 * var(--space-1-5));
  gap: var(--space-1-5);
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.p-month-days__day {
  display: inline-grid;
  min-width: 0;
  height: var(--control-height);
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
  font-weight: var(--weight-semibold);
  cursor: pointer;
}

.p-month-days__day:disabled {
  opacity: 0.5;
  cursor: default;
}

.p-month-days__day:hover:not(:disabled) {
  background: var(--color-fill);
}

.p-month-days__day--on,
.p-month-days__day--on:hover:not(:disabled) {
  border-color: var(--tone);
  background: var(--tone-container);
  color: var(--tone-on-container);
  box-shadow: var(--shadow-selected-inset);
}
</style>
