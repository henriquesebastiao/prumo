<script setup lang="ts">
/** The fields of a frequency (H2): fixed dates (every day, weekdays every N weeks, days of the
 * month or the Nth weekday every N months) or N times in a week, a fortnight or a month. */
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { PField, PMonthDayPicker, PSelect, PStepper, PSwitch, PText, PWeekdayPicker } from '@/ui'

import { weekdayName } from '../helpers'
import { PERIOD_DAYS, type DraftKind, type FrequencyDraft, type WeekOfMonth } from './frequency'

const draft = defineModel<FrequencyDraft>({ required: true })
const { t } = useI18n()

const kinds: DraftKind[] = ['daily', 'weekdays', 'month_days', 'month_weekday', 'per_period']
const kindOptions = computed(() =>
  kinds.map((value) => ({ value, label: t(`habits.frequency.kinds.${value}`) })),
)
const periodOptions = computed(() =>
  (['week', 'fortnight', 'month'] as const).map((value) => ({
    value,
    label: t(`habits.frequency.periods.${value}`),
  })),
)
const weekdayOptions = computed(() =>
  [0, 1, 2, 3, 4, 5, 6].map((value) => ({ value: String(value), label: weekdayName(t, value) })),
)
const weekOptions = computed(() =>
  ([1, 2, 3, 4, -1] as WeekOfMonth[]).map((value) => ({
    value: String(value),
    label: t(
      `habits.frequency.nth.${draft.value.weekday >= 5 ? 'm' : 'f'}.${value === -1 ? 'last' : value}`,
    ),
  })),
)
const preferredOptions = computed(() => {
  const none = { value: '-1', label: t('habits.form.noPreferred') }
  if (draft.value.period === 'month')
    return [
      none,
      ...Array.from({ length: 31 }, (_, index) => ({
        value: String(index + 1),
        label: t('habits.frequency.dayOfMonth', { day: index + 1 }),
      })),
    ]
  return [none, ...weekdayOptions.value]
})
const preferred = computed({
  get: () => String(draft.value.preferredDay ?? -1),
  set: (value: string) => update({ preferredDay: value === '-1' ? null : Number(value) }),
})
const maxTimes = computed(() => PERIOD_DAYS[draft.value.period])

function update(patch: Partial<FrequencyDraft>) {
  draft.value = { ...draft.value, ...patch }
}

// A preferred day of another kind of period would be refused: start over when the period changes.
watch(
  () => draft.value.period,
  (period, previous) => {
    if (previous && period !== previous && (period === 'month' || previous === 'month'))
      update({ preferredDay: null })
    if (draft.value.times > PERIOD_DAYS[period]) update({ times: PERIOD_DAYS[period] })
  },
)
</script>

<template>
  <div class="frequency">
    <PField :label="t('habits.form.frequency')">
      <PSelect
        :model-value="draft.kind"
        :options="kindOptions"
        @update:model-value="(kind: DraftKind) => update({ kind })"
      />
    </PField>

    <template v-if="draft.kind === 'weekdays'">
      <PField :label="t('habits.form.weekdays')" label-as="span">
        <PWeekdayPicker
          :model-value="draft.weekdays"
          tone="habits"
          @update:model-value="(weekdays: number[]) => update({ weekdays })"
        />
      </PField>
      <PField :label="t('habits.form.everyNWeeks')" label-as="span">
        <PStepper
          :model-value="draft.everyNWeeks"
          :min="1"
          :max="52"
          :label="t('habits.form.everyNWeeks')"
          @update:model-value="(everyNWeeks: number) => update({ everyNWeeks })"
        />
      </PField>
    </template>

    <template v-if="draft.kind === 'month_days'">
      <PField
        :label="t('habits.form.monthDays')"
        :hint="t('habits.form.monthDaysHint')"
        label-as="span"
      >
        <PMonthDayPicker
          :model-value="draft.monthDays"
          :label="t('habits.form.monthDays')"
          tone="habits"
          @update:model-value="(monthDays: number[]) => update({ monthDays })"
        />
      </PField>
      <div class="form__switch">
        <PText as="span">{{ t('habits.form.monthLastDay') }}</PText>
        <PSwitch
          :model-value="draft.monthLastDay"
          :label="t('habits.form.monthLastDay')"
          @update:model-value="(monthLastDay: boolean) => update({ monthLastDay })"
        />
      </div>
    </template>

    <div v-if="draft.kind === 'month_weekday'" class="form__row">
      <PField :label="t('habits.form.weekOfMonth')">
        <PSelect
          :model-value="String(draft.weekOfMonth)"
          :options="weekOptions"
          @update:model-value="
            (value: string) => update({ weekOfMonth: Number(value) as WeekOfMonth })
          "
        />
      </PField>
      <PField :label="t('habits.form.weekday')">
        <PSelect
          :model-value="String(draft.weekday)"
          :options="weekdayOptions"
          @update:model-value="(value: string) => update({ weekday: Number(value) })"
        />
      </PField>
    </div>

    <PField
      v-if="draft.kind === 'month_days' || draft.kind === 'month_weekday'"
      :label="t('habits.form.everyNMonths')"
      label-as="span"
    >
      <PStepper
        :model-value="draft.everyNMonths"
        :min="1"
        :max="12"
        :label="t('habits.form.everyNMonths')"
        @update:model-value="(everyNMonths: number) => update({ everyNMonths })"
      />
    </PField>

    <template v-if="draft.kind === 'per_period'">
      <div class="form__row">
        <PField :label="t('habits.form.times')" label-as="span">
          <PStepper
            :model-value="draft.times"
            :min="1"
            :max="maxTimes"
            :label="t('habits.form.times')"
            @update:model-value="(times: number) => update({ times })"
          />
        </PField>
        <PField :label="t('habits.form.period')">
          <PSelect
            :model-value="draft.period"
            :options="periodOptions"
            @update:model-value="(period: FrequencyDraft['period']) => update({ period })"
          />
        </PField>
      </div>
      <PField :label="t('habits.form.preferredDay')" :hint="t('habits.form.preferredHint')">
        <PSelect v-model="preferred" :options="preferredOptions" />
      </PField>
    </template>

    <PText
      v-if="draft.everyNWeeks > 1 || draft.everyNMonths > 1 || draft.period === 'fortnight'"
      variant="sm"
      tone="secondary"
      >{{ t('habits.form.anchorHint') }}</PText
    >
  </div>
</template>

<style src="./form.css" scoped></style>
<style scoped>
.frequency {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
</style>
