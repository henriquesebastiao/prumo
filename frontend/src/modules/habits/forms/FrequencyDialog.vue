<script setup lang="ts">
/** A new version of the frequency, from a day (today or later), or the edit of a future one (H2). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { PAlert, PButton, PDateInput, PDialog, PField, useToast } from '@/ui'

import { useSaveFrequency, type HabitFrequency } from '../api'
import { draftOf, draftValid, fieldsOf } from './frequency'
import FrequencyFields from './FrequencyFields.vue'
import { today as deviceToday } from './today'

const props = defineProps<{ habitId: string; frequency?: HabitFrequency; today?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveFrequency()
const saving = save.isPending

const draft = ref(draftOf())
const validFrom = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)
const first = computed(() => props.today ?? deviceToday())

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    draft.value = draftOf(props.frequency)
    validFrom.value = props.frequency?.valid_from ?? first.value
  },
  { immediate: true },
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      habitId: props.habitId,
      id: props.frequency?.id,
      body: { valid_from: validFrom.value, ...fieldsOf(draft.value) },
    })
    toast.show({ title: t('habits.form.saved.frequency') })
    open.value = false
  } catch (error) {
    errors.value = apiFieldErrors(error, { t, te })
    if (!Object.keys(errors.value).length) failure.value = errorMessage(error, { t, te })
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t(frequency ? 'habits.form.titles.editFrequency' : 'habits.form.titles.newFrequency')"
    icon="repeat"
    tone="habits"
  >
    <form id="frequency-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <FrequencyFields v-model="draft" />
      <PField
        v-if="!frequency"
        :label="t('habits.form.validFrom')"
        :hint="t('habits.form.validFromHint')"
        :error="errors.valid_from"
      >
        <PDateInput v-model="validFrom" :min="first" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="frequency-form"
        variant="primary"
        :loading="saving"
        :disabled="!validFrom || !draftValid(draft)"
        >{{ t('habits.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
