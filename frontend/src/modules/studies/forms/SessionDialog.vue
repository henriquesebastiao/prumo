<script setup lang="ts">
/**
 * "Registrar estudo" (quick action, Hoje and the subject page): subject, topic (created by name,
 * E10), duration in chips or typed, and the start, which defaults to "finished now".
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { isoToZoned, zonedToIso } from '@/lib/format'
import {
  PAlert,
  PButton,
  PChipChoice,
  PCombobox,
  PDateInput,
  PDialog,
  PField,
  PNumberInput,
  PSelect,
  PText,
  useToast,
} from '@/ui'

import { useSaveSession, useSubject, useSubjects, type StudySession } from '../api'
import { QUICK_MINUTES } from '../helpers'

const props = defineProps<{ subjectId?: string; session?: StudySession }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveSession()
const subjects = useSubjects()

const chosenSubject = ref('')
const topicValue = ref<string | null>(null)
const createdTopic = ref<string | null>(null)
const chip = ref<string>('30')
const customMinutes = ref<number | null>(null)
const day = ref('')
const time = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)
const NEW = 'new:'

const detail = useSubject(() => chosenSubject.value || '00000000-0000-0000-0000-000000000000')
const subjectOptions = computed(() =>
  (subjects.data.value ?? []).map((s) => ({
    value: s.id,
    label: s.name,
    description: s.area_name,
  })),
)
const topicOptions = computed(() => [
  ...(chosenSubject.value && detail.data.value?.id === chosenSubject.value
    ? detail.data.value.topics
    : []
  ).map((topic) => ({ value: topic.id, label: topic.name })),
  ...(createdTopic.value
    ? [{ value: `${NEW}${createdTopic.value}`, label: createdTopic.value }]
    : []),
])
const chips = computed(() => [
  ...QUICK_MINUTES.map((m) => ({ value: String(m), label: `${m} ${t('studies.form.minutes')}` })),
  { value: 'other', label: t('studies.form.otherDuration') },
])
const duration = computed(() =>
  chip.value === 'other' ? (customMinutes.value ?? 0) : Number(chip.value),
)

/** "Finished now": the start is now minus the duration, in the user's zone. */
function finishedNow() {
  const when = isoToZoned(new Date(Date.now() - duration.value * 60_000))
  day.value = when.day
  time.value = when.time
}

function reset() {
  errors.value = {}
  failure.value = null
  createdTopic.value = null
  const session = props.session
  chosenSubject.value = session?.subject.id ?? props.subjectId ?? subjects.data.value?.[0]?.id ?? ''
  topicValue.value = session?.topic?.id ?? null
  if (session) {
    const known = QUICK_MINUTES.includes(session.duration_minutes)
    chip.value = known ? String(session.duration_minutes) : 'other'
    customMinutes.value = known ? null : session.duration_minutes
    const when = isoToZoned(session.started_at)
    day.value = when.day
    time.value = when.time
  } else {
    chip.value = '30'
    customMinutes.value = null
    finishedNow()
  }
}
watch(open, (value) => value && reset(), { immediate: true })
watch(subjectOptions, (options) => {
  if (!chosenSubject.value && options[0]) chosenSubject.value = options[0].value
})
watch(chosenSubject, () => {
  if (!props.session || props.session.subject.id !== chosenSubject.value) topicValue.value = null
})
watch(duration, () => {
  if (!props.session) finishedNow()
})

function createTopic(term: string) {
  createdTopic.value = term
  topicValue.value = `${NEW}${term}`
}

async function submit() {
  errors.value = {}
  failure.value = null
  const topic = topicValue.value
  const body = {
    subject_id: chosenSubject.value,
    topic_id: topic && !topic.startsWith(NEW) ? topic : null,
    topic_name: topic?.startsWith(NEW) ? topic.slice(NEW.length) : null,
    started_at: zonedToIso(day.value, time.value),
    duration_minutes: duration.value,
  }
  try {
    await save.mutateAsync({ id: props.session?.id, body })
    toast.show({ title: t('studies.form.saved.session') })
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
    :title="t(session ? 'studies.form.titles.editSession' : 'studies.form.titles.newSession')"
    icon="graduation-cap"
    tone="studies"
    size="s"
  >
    <form id="session-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="subjects.isSuccess.value && !subjectOptions.length" tone="secondary">{{
        t('studies.form.noSubjects')
      }}</PText>
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('studies.form.subject')" :error="errors.subject_id">
        <PSelect v-model="chosenSubject" :options="subjectOptions" />
      </PField>
      <PField :label="t('studies.form.topic')" optional :error="errors.topic_name">
        <PCombobox
          v-model="topicValue"
          :options="topicOptions"
          :placeholder="t('studies.form.topicPlaceholder')"
          :create-label="(term) => t('studies.form.topicCreate', { name: term })"
          tone="studies"
          @create="createTopic"
        />
      </PField>
      <PField :label="t('studies.form.duration')" label-as="span" :error="errors.duration_minutes">
        <PChipChoice
          v-model="chip"
          :options="chips"
          :label="t('studies.form.duration')"
          tone="studies"
        />
        <PNumberInput
          v-if="chip === 'other'"
          v-model="customMinutes"
          :suffix="t('studies.form.minutes')"
          class="form__pages"
        />
      </PField>
      <div class="form__row">
        <PField
          :label="t('studies.form.date')"
          :hint="t('studies.form.startHint')"
          :error="errors.started_at"
        >
          <PDateInput v-model="day" />
        </PField>
        <PField :label="t('studies.form.time')">
          <PDateInput v-model="time" type="time" />
        </PField>
      </div>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="session-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!chosenSubject || !duration || !day || !time"
        >{{ t('studies.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
