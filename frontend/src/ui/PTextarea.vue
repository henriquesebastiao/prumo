<script setup lang="ts">
import { useField } from './field'

const props = withDefaults(
  defineProps<{ placeholder?: string; rows?: number; invalid?: boolean; id?: string }>(),
  { placeholder: undefined, rows: 4, id: undefined },
)
const model = defineModel<string>({ default: '' })
const field = useField(props)
</script>

<template>
  <div class="p-control p-textarea" :class="{ 'p-control--invalid': field.invalid.value }">
    <textarea
      :id="field.id.value"
      v-model="model"
      class="p-textarea__input"
      :rows="rows"
      :placeholder="placeholder"
      :aria-invalid="field.invalid.value || undefined"
      :aria-describedby="field.describedBy.value"
    />
  </div>
</template>

<style src="./control.css"></style>

<style scoped>
.p-textarea {
  height: auto;
  align-items: stretch;
  padding: var(--space-2-5) var(--space-3-5);
}

.p-textarea__input {
  flex: 1;
  min-height: 110px;
  border: 0;
  outline: 0;
  resize: vertical;
  background: transparent;
  color: inherit;
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

.p-textarea__input::placeholder {
  color: var(--color-text-muted);
}
</style>
