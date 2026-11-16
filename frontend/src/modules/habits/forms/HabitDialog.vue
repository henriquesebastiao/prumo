<script setup lang="ts">
/** New or edited habit. The kind and the measure are chosen once, when it is created. */
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
  PIconPicker,
  PInput,
  PNumberInput,
  PSegmented,
  PSwatchPicker,
  PText,
  useToast,
} from '@/ui'

import { useSaveHabit, type Habit, type HabitColor } from '../api'
import { iconOptions, swatchOptions } from '../helpers'
import { draftOf, draftValid, fieldsOf } from './frequency'
import FrequencyFields from './FrequencyFields.vue'
import { today } from './today'

const props = defineProps<{ habit?: Habit }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveHabit()
// Exposed as its own ref: vue-tsc loses the mutation's type in this template otherwise.
const saving = save.isPending

const name = ref('')
const kind = ref<'build' | 'quit'>('build')
const icon = ref('sparkles')
const color = ref('amber')
const measure = ref<'check' | 'quantity'>('check')
const target = ref<number | null>(null)
const unit = ref('')
const startedOn = ref('')
const frequency = ref(draftOf())
const timeOfDay = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

const editing = computed(() => Boolean(props.habit))
const isBuild = computed(() => (props.habit?.kind ?? kind.value) === 'build')
const isQuantity = computed(
  () => isBuild.value && (props.habit?.measure ?? measure.value) === 'quantity',
)

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    const habit = props.habit
    name.value = habit?.name ?? ''
    kind.value = (habit?.kind as 'build' | 'quit' | undefined) ?? 'build'
    icon.value = habit?.icon ?? 'sparkles'
    color.value = habit?.color ?? 'amber'
    measure.value = (habit?.measure as 'check' | 'quantity' | null | undefined) ?? 'check'
    target.value = habit?.target_value ?? null
    unit.value = habit?.unit ?? ''
    startedOn.value = habit?.started_on ?? today()
    frequency.value = draftOf()
    timeOfDay.value = habit?.time_of_day ?? ''
  },
  { immediate: true },
)

const kindOptions = computed(() => [
  { value: 'build' as const, label: t('habits.kinds.build') },
  { value: 'quit' as const, label: t('habits.kinds.quit') },
])
const measureOptions = computed(() => [
  { value: 'check' as const, label: t('habits.measures.check') },
  { value: 'quantity' as const, label: t('habits.measures.quantity') },
])

const valid = computed(
  () =>
    Boolean(name.value.trim()) &&
    (!isQuantity.value || (Boolean(target.value) && Boolean(unit.value.trim()))) &&
    (editing.value || !isBuild.value || draftValid(frequency.value)),
)

async function submit() {
  errors.value = {}
  failure.value = null
  const quantity = isQuantity.value
    ? { target_value: target.value ?? undefined, unit: unit.value.trim() }
    : {}
  const base = {
    name: name.value.trim(),
    icon: icon.value,
    color: color.value as HabitColor,
    started_on: startedOn.value,
    time_of_day: timeOfDay.value || null,
    ...quantity,
  }
  try {
    if (props.habit) {
      await save.mutateAsync({ id: props.habit.id, body: base })
    } else {
      await save.mutateAsync({
        body: {
          ...base,
          kind: kind.value,
          ...(kind.value === 'build'
            ? {
                measure: measure.value,
                frequency: fieldsOf(frequency.value),
              }
            : {}),
        },
      })
    }
    toast.show({ title: t('habits.form.saved.habit') })
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
    :title="t(habit ? 'habits.form.titles.editHabit' : 'habits.form.titles.newHabit')"
    icon="list-checks"
    tone="habits"
  >
    <form id="habit-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField v-if="!habit" :label="t('habits.form.kind')" label-as="span">
        <PSegmented v-model="kind" :options="kindOptions" :label="t('habits.form.kind')" block />
        <PText variant="sm" tone="secondary">{{
          t(kind === 'build' ? 'habits.kinds.buildHint' : 'habits.kinds.quitHint')
        }}</PText>
      </PField>
      <PField :label="t('habits.form.name')" :error="errors.name">
        <PInput v-model="name" />
      </PField>
      <PField :label="t('habits.form.icon')" label-as="span" :error="errors.icon">
        <PIconPicker
          v-model="icon"
          :options="iconOptions(t)"
          :label="t('habits.form.icon')"
          tone="habits"
        />
      </PField>
      <PField :label="t('habits.form.color')" label-as="span" :error="errors.color">
        <PSwatchPicker
          v-model="color"
          :options="swatchOptions(t, color)"
          :label="t('habits.form.color')"
        />
      </PField>
      <PField v-if="isBuild && !habit" :label="t('habits.form.measure')" label-as="span">
        <PSegmented
          v-model="measure"
          :options="measureOptions"
          :label="t('habits.form.measure')"
          block
        />
      </PField>
      <div v-if="isQuantity" class="form__row">
        <PField :label="t('habits.form.target')" :error="errors.target_value">
          <PNumberInput v-model="target" />
        </PField>
        <PField
          :label="t('habits.form.unit')"
          :hint="t('habits.form.unitHint')"
          :error="errors.unit"
        >
          <PInput v-model="unit" :maxlength="12" />
        </PField>
      </div>
      <FrequencyFields v-if="isBuild && !habit" v-model="frequency" />
      <PField
        :label="t('habits.form.startedOn')"
        :hint="t('habits.form.startedOnHint')"
        :error="errors.started_on"
      >
        <PDateInput v-model="startedOn" :max="today()" />
      </PField>
      <PField
        :label="t('habits.form.timeOfDay')"
        :hint="t('habits.form.timeOfDayHint')"
        :error="errors.time_of_day"
      >
        <PDateInput v-model="timeOfDay" type="time" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="habit-form"
        variant="primary"
        :loading="saving"
        :disabled="!valid"
        >{{ t('habits.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
