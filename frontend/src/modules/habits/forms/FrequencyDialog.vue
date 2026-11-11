<script setup lang="ts">
/** A new version of the frequency, from a day (today or later), or the edit of a future one (H2). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import {
  PAlert,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PSegmented,
  PStepper,
  PWeekdayPicker,
  useToast,
} from '@/ui'

import { useSaveFrequency, type FrequencyKind, type HabitFrequency } from '../api'
import { today as deviceToday } from './today'

const props = defineProps<{ habitId: string; frequency?: HabitFrequency; today?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveFrequency()
const saving = save.isPending

const kind = ref<FrequencyKind>('daily')
const times = ref(3)
const weekdays = ref<number[]>([])
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
    kind.value = props.frequency?.kind ?? 'daily'
    times.value = props.frequency?.times_per_week ?? 3
    weekdays.value = props.frequency?.weekdays ?? [0, 1, 2, 3, 4]
    validFrom.value = props.frequency?.valid_from ?? first.value
  },
  { immediate: true },
)

const options = computed(() =>
  (['daily', 'weekly', 'weekdays'] as const).map((value) => ({
    value,
    label: t(`habits.frequency.kinds.${value}`),
  })),
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      habitId: props.habitId,
      id: props.frequency?.id,
      body: {
        valid_from: validFrom.value,
        kind: kind.value,
        times_per_week: kind.value === 'weekly' ? times.value : null,
        weekdays: kind.value === 'weekdays' ? weekdays.value : null,
      },
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
    size="s"
  >
    <form id="frequency-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PSegmented v-model="kind" :options="options" :label="t('habits.form.frequency')" block />
      <PField v-if="kind === 'weekly'" :label="t('habits.form.timesPerWeek')" label-as="span">
        <PStepper v-model="times" :min="1" :max="7" :label="t('habits.form.timesPerWeek')" />
      </PField>
      <PField v-if="kind === 'weekdays'" :label="t('habits.form.weekdays')" label-as="span">
        <PWeekdayPicker v-model="weekdays" tone="habits" />
      </PField>
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
        :disabled="!validFrom || (kind === 'weekdays' && !weekdays.length)"
        >{{ t('habits.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
