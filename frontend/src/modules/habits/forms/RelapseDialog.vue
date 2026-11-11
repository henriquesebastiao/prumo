<script setup lang="ts">
/** A relapse of a habit to quit (H7): when (now by default) and, if wanted, what came before. */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { isoToZoned, zonedToIso } from '@/lib/format'
import { PAlert, PButton, PDateInput, PDialog, PField, PTextarea, useToast } from '@/ui'

import { useLogRelapse } from '../api'

const props = defineProps<{ habitId: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useLogRelapse()
const saving = save.isPending

const day = ref('')
const time = ref('')
const note = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    const now = isoToZoned(new Date().toISOString())
    day.value = now.day
    time.value = now.time
    note.value = ''
  },
  { immediate: true },
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      habitId: props.habitId,
      body: { occurred_at: zonedToIso(day.value, time.value), note: note.value.trim() || null },
    })
    toast.show({ title: t('habits.form.saved.relapse') })
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
    :title="t('habits.form.titles.relapse')"
    icon="refresh"
    tone="habits"
    size="s"
  >
    <form id="relapse-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('habits.form.occurredAt')" :error="errors.occurred_at">
          <PDateInput v-model="day" />
        </PField>
        <PField :label="t('habits.form.time')">
          <PDateInput v-model="time" type="time" />
        </PField>
      </div>
      <PField :label="t('habits.form.note')" :error="errors.note" optional>
        <PTextarea v-model="note" :rows="3" :placeholder="t('habits.form.notePlaceholder')" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="relapse-form"
        variant="primary"
        :loading="saving"
        :disabled="!day || !time"
        >{{ t('habits.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
