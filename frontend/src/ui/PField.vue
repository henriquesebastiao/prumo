<script setup lang="ts">
import { computed, useId } from 'vue'
import { useI18n } from 'vue-i18n'

import { provideField } from './field'

const props = withDefaults(
  defineProps<{
    label?: string
    hint?: string
    error?: string
    optional?: boolean
    id?: string
    /** Renders the label as text (for groups such as segmented controls or switches). */
    labelAs?: 'label' | 'span'
  }>(),
  { label: undefined, hint: undefined, error: undefined, id: undefined, labelAs: 'label' },
)

const { t } = useI18n()
const autoId = useId()
const fieldId = computed(() => props.id ?? `field-${autoId}`)
const messageId = computed(() => `${fieldId.value}-message`)

provideField({
  id: fieldId,
  describedBy: computed(() => (props.error || props.hint ? messageId.value : undefined)),
  invalid: computed(() => Boolean(props.error)),
})
</script>

<template>
  <div class="p-field">
    <component
      :is="labelAs"
      v-if="label"
      :id="`${fieldId}-label`"
      class="p-field__label"
      :for="labelAs === 'label' ? fieldId : undefined"
    >
      {{ label }}<span v-if="optional" class="p-field__optional"> · {{ t('ui.optional') }}</span>
    </component>
    <slot :id="fieldId" :label-id="`${fieldId}-label`" />
    <p v-if="error" :id="messageId" class="p-field__error">{{ error }}</p>
    <p v-else-if="hint" :id="messageId" class="p-field__hint">{{ hint }}</p>
  </div>
</template>

<style scoped>
.p-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-1-5);
}

.p-field__label {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}

.p-field__optional {
  color: var(--color-text-muted);
  font-weight: var(--weight-medium);
}

.p-field__hint {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.p-field__error {
  color: var(--color-danger);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}
</style>
