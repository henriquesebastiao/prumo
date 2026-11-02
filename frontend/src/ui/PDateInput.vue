<script setup lang="ts">
import { useField } from './field'
import PIcon from './PIcon.vue'

const props = withDefaults(
  defineProps<{
    /** `date`: `YYYY-MM-DD`. `time`: `HH:MM`. */
    type?: 'date' | 'time'
    invalid?: boolean
    disabled?: boolean
    min?: string
    max?: string
    id?: string
  }>(),
  { type: 'date', min: undefined, max: undefined, id: undefined },
)

const model = defineModel<string>({ default: '' })
const field = useField(props)
</script>

<template>
  <div
    class="p-control"
    :class="{ 'p-control--invalid': field.invalid.value, 'p-control--disabled': disabled }"
  >
    <PIcon :name="type === 'time' ? 'clock' : 'calendar'" size="sm" class="p-control__icon" />
    <input
      :id="field.id.value"
      v-model="model"
      class="p-control__input p-date-input"
      :type="type"
      :min="min"
      :max="max"
      :disabled="disabled"
      :aria-invalid="field.invalid.value || undefined"
      :aria-describedby="field.describedBy.value"
    />
  </div>
</template>

<style src="./control.css"></style>

<style scoped>
.p-date-input::-webkit-calendar-picker-indicator {
  opacity: 0.6;
  cursor: pointer;
}
</style>
