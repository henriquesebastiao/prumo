<script setup lang="ts">
/** Week navigator: ‹ 16/11 a 22/11 ›. The model is the Monday of the week as `YYYY-MM-DD`. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort } from '@/lib/format'

import PIcon from './PIcon.vue'

const props = withDefaults(
  defineProps<{
    label: string
    /** Monday of the last week that can be shown. */
    max?: string
    /** Monday of the current week: shown as "Esta semana". */
    current?: string
  }>(),
  { max: undefined, current: undefined },
)
const model = defineModel<string>({ required: true })
const { t } = useI18n()

function shift(monday: string, weeks: number): string {
  const [year, month, day] = monday.split('-').map(Number) as [number, number, number]
  const date = new Date(Date.UTC(year, month - 1, day + weeks * 7))
  return date.toISOString().slice(0, 10)
}

const sunday = computed(() => {
  const [year, month, day] = model.value.split('-').map(Number) as [number, number, number]
  return new Date(Date.UTC(year, month - 1, day + 6)).toISOString().slice(0, 10)
})
const text = computed(() =>
  props.current && model.value === props.current
    ? t('ui.thisWeek')
    : t('ui.weekOf', { start: dateShort(model.value), end: dateShort(sunday.value) }),
)
const atMax = computed(() => props.max !== undefined && model.value >= props.max)
</script>

<template>
  <div class="p-week-nav" role="group" :aria-label="label">
    <button
      type="button"
      class="p-week-nav__step"
      :aria-label="t('ui.previousWeek')"
      @click="model = shift(model, -1)"
    >
      <PIcon name="chevron-left" size="sm" />
    </button>
    <span class="p-week-nav__label" aria-live="polite">{{ text }}</span>
    <button
      type="button"
      class="p-week-nav__step"
      :aria-label="t('ui.nextWeek')"
      :disabled="atMax"
      @click="model = shift(model, 1)"
    >
      <PIcon name="chevron-right" size="sm" />
    </button>
  </div>
</template>

<style scoped>
.p-week-nav {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.p-week-nav__step {
  display: inline-grid;
  width: var(--control-height);
  height: var(--control-height);
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.p-week-nav__step:disabled {
  opacity: 0.4;
  cursor: default;
}

.p-week-nav__step:hover:not(:disabled) {
  background: var(--color-fill);
  color: var(--color-text);
}

.p-week-nav__label {
  min-width: 10.5rem;
  text-align: center;
  font-weight: var(--weight-semibold);
  font-variant-numeric: tabular-nums;
}
</style>
