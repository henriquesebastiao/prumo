<script setup lang="ts">
/** Month navigator: ‹ Novembro de 2026 ›. The model is a month as `YYYY-MM`. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { monthYear } from '@/lib/format'

import PIcon from './PIcon.vue'

const props = withDefaults(defineProps<{ label: string; max?: string }>(), { max: undefined })
const model = defineModel<string>({ required: true })
const { t } = useI18n()

function shift(month: string, delta: number): string {
  const [year, index] = month.split('-').map(Number) as [number, number]
  const date = new Date(Date.UTC(year, index - 1 + delta, 1))
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
}

const text = computed(() => monthYear(`${model.value}-01`))
const atMax = computed(() => props.max !== undefined && model.value >= props.max)
</script>

<template>
  <div class="p-month-nav" role="group" :aria-label="label">
    <button
      type="button"
      class="p-month-nav__step"
      :aria-label="t('ui.previousMonth')"
      @click="model = shift(model, -1)"
    >
      <PIcon name="chevron-left" size="sm" />
    </button>
    <span class="p-month-nav__label" aria-live="polite">{{ text }}</span>
    <button
      type="button"
      class="p-month-nav__step"
      :aria-label="t('ui.nextMonth')"
      :disabled="atMax"
      @click="model = shift(model, 1)"
    >
      <PIcon name="chevron-right" size="sm" />
    </button>
  </div>
</template>

<style scoped>
.p-month-nav {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: var(--control-height-lg);
  padding: 0 var(--space-1-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
}

.p-month-nav__label {
  min-width: 11ch;
  padding: 0 var(--space-2);
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  text-align: center;
  white-space: nowrap;
}

.p-month-nav__step {
  display: inline-grid;
  width: var(--control-height-sm);
  height: var(--control-height-sm);
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.p-month-nav__step:disabled {
  opacity: 0.4;
  cursor: default;
}

.p-month-nav__step:hover:not(:disabled) {
  background: var(--color-fill);
}
</style>
