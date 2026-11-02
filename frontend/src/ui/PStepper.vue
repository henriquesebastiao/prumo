<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useField } from './field'
import { formatLocaleNumber, parseLocaleNumber } from './number'
import PIcon from './PIcon.vue'

const props = withDefaults(
  defineProps<{
    min?: number
    max?: number
    step?: number
    /** Short text before the value, such as `p.` for pages. */
    prefix?: string
    label?: string
    id?: string
  }>(),
  {
    min: 0,
    max: Number.MAX_SAFE_INTEGER,
    step: 1,
    prefix: undefined,
    label: undefined,
    id: undefined,
  },
)

const model = defineModel<number>({ default: 0 })
const field = useField(props)
const { t } = useI18n()
const text = computed(() => formatLocaleNumber(model.value, 0))

function clamp(value: number) {
  return Math.min(props.max, Math.max(props.min, value))
}

function change(delta: number) {
  model.value = clamp(model.value + delta)
}

function onInput(event: Event) {
  const parsed = parseLocaleNumber((event.target as HTMLInputElement).value)
  if (parsed !== null) model.value = clamp(Math.round(parsed))
}
</script>

<template>
  <div class="p-stepper">
    <button
      type="button"
      class="p-stepper__button"
      :aria-label="t('ui.decrease')"
      :disabled="model <= min"
      @click="change(-step)"
    >
      <PIcon name="minus" size="sm" />
    </button>
    <label class="p-stepper__field">
      <span v-if="prefix" class="p-stepper__prefix">{{ prefix }}</span>
      <input
        :id="field.id.value"
        class="p-stepper__input"
        :value="text"
        inputmode="numeric"
        :aria-label="label"
        :aria-describedby="field.describedBy.value"
        @change="onInput"
        @keydown.up.prevent="change(step)"
        @keydown.down.prevent="change(-step)"
      />
    </label>
    <button
      type="button"
      class="p-stepper__button"
      :aria-label="t('ui.increase')"
      :disabled="model >= max"
      @click="change(step)"
    >
      <PIcon name="add" size="sm" />
    </button>
  </div>
</template>

<style scoped>
.p-stepper {
  display: flex;
  flex: 1;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.p-stepper__button {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: var(--control-height);
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text);
}

.p-stepper__button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.p-stepper__field {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-width: 0;
  height: var(--control-height);
  padding: 0 var(--space-4);
  border-radius: var(--radius-full);
  background: var(--color-surface-inset);
}

.p-stepper__field:focus-within {
  outline: var(--focus-width) solid var(--color-focus);
  outline-offset: 2px;
}

.p-stepper__prefix {
  color: var(--color-text-muted);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
}

.p-stepper__input {
  width: 5ch;
  min-width: 0;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: inherit;
  font-size: var(--text-2xl);
  font-weight: var(--weight-heavy);
  letter-spacing: var(--tracking-snug);
}
</style>
