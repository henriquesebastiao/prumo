<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useField } from './field'
import type { IconName } from './icons'
import PIcon from './PIcon.vue'

const props = withDefaults(
  defineProps<{
    type?: 'text' | 'password' | 'email' | 'search' | 'url' | 'tel'
    placeholder?: string
    prefix?: string
    suffix?: string
    icon?: IconName
    invalid?: boolean
    readonly?: boolean
    disabled?: boolean
    /** Shows a button that reveals the password. */
    revealable?: boolean
    /** Dashed look for values computed from other fields. */
    calculated?: boolean
    align?: 'start' | 'end'
    autocomplete?: string
    inputmode?: 'text' | 'numeric' | 'decimal' | 'email' | 'search' | 'tel' | 'url'
    id?: string
    maxlength?: number
  }>(),
  {
    type: 'text',
    placeholder: undefined,
    prefix: undefined,
    suffix: undefined,
    icon: undefined,
    align: 'start',
    autocomplete: undefined,
    inputmode: undefined,
    id: undefined,
    maxlength: undefined,
  },
)

const model = defineModel<string>({ default: '' })
const emit = defineEmits<{ blur: [FocusEvent]; focus: [FocusEvent] }>()
const field = useField(props)
const revealed = ref(false)
const input = ref<HTMLInputElement>()
const { t } = useI18n()

defineExpose({ focus: () => input.value?.focus(), select: () => input.value?.select() })
</script>

<template>
  <div
    class="p-control"
    :class="{
      'p-control--invalid': field.invalid.value,
      'p-control--calculated': calculated,
      'p-control--disabled': disabled,
    }"
  >
    <PIcon v-if="icon" :name="icon" size="sm" class="p-control__icon" />
    <span v-if="prefix" class="p-control__affix">{{ prefix }}</span>
    <input
      :id="field.id.value"
      ref="input"
      v-model="model"
      class="p-control__input"
      :class="{ 'p-input--end': align === 'end' }"
      :type="revealable && revealed ? 'text' : type"
      :placeholder="placeholder"
      :readonly="readonly"
      :disabled="disabled"
      :autocomplete="autocomplete"
      :inputmode="inputmode"
      :maxlength="maxlength"
      :aria-invalid="field.invalid.value || undefined"
      :aria-describedby="field.describedBy.value"
      @blur="emit('blur', $event)"
      @focus="emit('focus', $event)"
    />
    <span v-if="suffix" class="p-control__affix">{{ suffix }}</span>
    <button
      v-if="revealable"
      type="button"
      class="p-input__reveal"
      :aria-label="t(revealed ? 'ui.hidePassword' : 'ui.showPassword')"
      :aria-pressed="revealed"
      @click="revealed = !revealed"
    >
      <PIcon :name="revealed ? 'eye-off' : 'eye'" size="sm" />
    </button>
    <slot name="end" />
  </div>
</template>

<style src="./control.css"></style>

<style scoped>
.p-input--end {
  text-align: right;
}

.p-input__reveal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height-sm);
  height: var(--control-height-sm);
  margin-right: calc(var(--space-2) * -1);
  border: 0;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
}

.p-input__reveal:hover {
  background: var(--color-fill);
}
</style>
