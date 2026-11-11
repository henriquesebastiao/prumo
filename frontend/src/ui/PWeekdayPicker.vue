<script setup lang="ts">
/** Days of the week to pick (several): S T Q Q S S D. The model holds 0 = Monday … 6 = Sunday. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Tone } from './types'

const props = withDefaults(defineProps<{ label?: string; tone?: Tone; disabled?: boolean }>(), {
  label: undefined,
  tone: 'accent',
  disabled: false,
})
const model = defineModel<number[]>({ default: () => [] })
const { t, tm } = useI18n()

const shorts = computed(() => tm('ui.weekdays.short') as string[])
const longs = computed(() => tm('ui.weekdays.long') as string[])

function toggle(day: number) {
  if (props.disabled) return
  const set = new Set(model.value)
  if (set.has(day)) set.delete(day)
  else set.add(day)
  model.value = [...set].sort((a, b) => a - b)
}
</script>

<template>
  <div
    class="p-weekdays"
    role="group"
    :aria-label="label ?? t('ui.weekdays.label')"
    :data-tone="tone"
  >
    <button
      v-for="(short, day) in shorts"
      :key="day"
      type="button"
      class="p-weekdays__day"
      :class="{ 'p-weekdays__day--on': model.includes(day) }"
      :aria-pressed="model.includes(day)"
      :aria-label="longs[day]"
      :title="longs[day]"
      :disabled="disabled"
      @click="toggle(day)"
    >
      {{ short }}
    </button>
  </div>
</template>

<style scoped>
.p-weekdays {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1-5);
}

.p-weekdays__day {
  display: inline-grid;
  width: var(--control-height);
  height: var(--control-height);
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-weight: var(--weight-semibold);
  cursor: pointer;
}

.p-weekdays__day:disabled {
  opacity: 0.5;
  cursor: default;
}

.p-weekdays__day:hover:not(:disabled) {
  background: var(--color-fill);
}

.p-weekdays__day--on,
.p-weekdays__day--on:hover:not(:disabled) {
  border-color: var(--tone);
  background: var(--tone-container);
  color: var(--tone-on-container);
  box-shadow: var(--shadow-selected-inset);
}
</style>
