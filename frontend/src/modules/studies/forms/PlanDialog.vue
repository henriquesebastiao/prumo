<script setup lang="ts">
/**
 * A version of the plan (E1): its blocks (subject, weekdays, optional time, duration) and, for a
 * new version, the date it starts (today or later; next Monday by default). With `plan`, edits
 * that version; with `base`, starts a new version from its blocks.
 */
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
  PIconButton,
  PNumberInput,
  PSelect,
  PText,
  PWeekdayPicker,
  useToast,
} from '@/ui'

import { useSavePlan, useSubjects, type Plan } from '../api'
import { nextMonday } from '../helpers'
import { today } from './today'

interface Draft {
  key: number
  subject_id: string
  weekdays: number[]
  starts_at: string
  duration_minutes: number | null
}

const props = defineProps<{ plan?: Plan; base?: Plan }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSavePlan()
const subjects = useSubjects()

const validFrom = ref('')
const blocks = ref<Draft[]>([])
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)
let keys = 0

const subjectOptions = computed(() =>
  (subjects.data.value ?? []).map((s) => ({
    value: s.id,
    label: s.name,
    description: s.area_name,
  })),
)

function fromPlan(plan: Plan | undefined): Draft[] {
  return (plan?.blocks ?? []).map((block) => ({
    key: keys++,
    subject_id: block.subject.id,
    weekdays: [...block.weekdays],
    starts_at: block.starts_at ? block.starts_at.slice(0, 5) : '',
    duration_minutes: block.duration_minutes,
  }))
}

function add() {
  blocks.value.push({
    key: keys++,
    subject_id: subjectOptions.value[0]?.value ?? '',
    weekdays: [],
    starts_at: '',
    duration_minutes: 30,
  })
}

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    validFrom.value = props.plan?.valid_from ?? nextMonday(today())
    blocks.value = fromPlan(props.plan ?? props.base)
    if (!blocks.value.length) add()
  },
  { immediate: true },
)

const valid = computed(
  () =>
    blocks.value.length > 0 &&
    blocks.value.every((b) => b.subject_id && b.weekdays.length && (b.duration_minutes ?? 0) > 0),
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      id: props.plan?.id,
      valid_from: validFrom.value,
      blocks: blocks.value.map((b) => ({
        subject_id: b.subject_id,
        weekdays: b.weekdays,
        starts_at: b.starts_at ? `${b.starts_at}:00` : null,
        duration_minutes: b.duration_minutes ?? 0,
      })),
    })
    toast.show({ title: t('studies.form.saved.plan') })
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
    :title="t(plan ? 'studies.form.titles.editPlan' : 'studies.form.titles.newPlan')"
    icon="calendar"
    tone="studies"
    size="m"
  >
    <form id="plan-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField
        :label="t('studies.form.validFrom')"
        :hint="plan ? undefined : t('studies.form.validFromHint')"
        :error="errors.valid_from"
      >
        <PDateInput
          v-model="validFrom"
          :min="today()"
          :disabled="Boolean(plan)"
          class="form__pages"
        />
      </PField>
      <PText variant="overline">{{ t('studies.form.blocks') }}</PText>
      <PText v-if="!blocks.length" tone="secondary">{{ t('studies.form.noBlocks') }}</PText>
      <fieldset v-for="(block, index) in blocks" :key="block.key" class="block">
        <legend class="block__legend">
          <span>{{ t('studies.form.block', { n: index + 1 }) }}</span>
          <PIconButton
            icon="trash"
            :label="t('studies.form.removeBlock')"
            variant="ghost"
            size="sm"
            @click="blocks.splice(index, 1)"
          />
        </legend>
        <div class="form__row">
          <PField :label="t('studies.form.subject')">
            <PSelect v-model="block.subject_id" :options="subjectOptions" />
          </PField>
          <PField :label="t('studies.form.duration')">
            <PNumberInput v-model="block.duration_minutes" :suffix="t('studies.form.minutes')" />
          </PField>
          <PField :label="t('studies.form.startsAt')" optional>
            <PDateInput v-model="block.starts_at" type="time" />
          </PField>
        </div>
        <PField :label="t('studies.form.weekdays')" label-as="span">
          <PWeekdayPicker v-model="block.weekdays" tone="studies" />
        </PField>
      </fieldset>
      <PButton variant="dashed" icon="add" :disabled="!subjectOptions.length" @click="add">{{
        t('studies.form.addBlock')
      }}</PButton>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="plan-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!valid || !validFrom"
        >{{ t('studies.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>

<style scoped>
.block {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin: 0;
  padding: var(--space-3) var(--space-4) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.block__legend {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0 var(--space-1);
  font-weight: var(--weight-semibold);
}
</style>
