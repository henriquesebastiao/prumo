<script setup lang="ts">
/** A pause from a day, with an end or open. */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { PAlert, PButton, PDateInput, PDialog, PField, useToast } from '@/ui'

import { useSavePause } from '../api'
import { today as deviceToday } from './today'

const props = defineProps<{ habitId: string; today?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSavePause()
const saving = save.isPending

const startsOn = ref('')
const endsOn = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    startsOn.value = props.today ?? deviceToday()
    endsOn.value = ''
  },
  { immediate: true },
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      habitId: props.habitId,
      body: { starts_on: startsOn.value, ends_on: endsOn.value || null },
    })
    toast.show({ title: t('habits.form.saved.pause') })
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
    :title="t('habits.form.titles.newPause')"
    icon="pause"
    tone="habits"
    size="s"
  >
    <form id="pause-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('habits.form.startsOn')" :error="errors.starts_on">
          <PDateInput v-model="startsOn" />
        </PField>
        <PField
          :label="t('habits.form.endsOn')"
          :hint="t('habits.form.endsOnHint')"
          :error="errors.ends_on"
          optional
        >
          <PDateInput v-model="endsOn" :min="startsOn" />
        </PField>
      </div>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="pause-form"
        variant="primary"
        :loading="saving"
        :disabled="!startsOn"
        >{{ t('habits.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
