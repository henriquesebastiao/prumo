<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort } from '@/lib/format'
import {
  PBadge,
  PCard,
  PList,
  PListItem,
  PQueryState,
  PStatCard,
  PText,
  PTile,
  PWeekNav,
} from '@/ui'

import { useWeek, type Day } from '../api'
import DayRows from '../components/DayRows.vue'
import { colorTone, minutes, mondayOf } from '../helpers'

const { t, tm } = useI18n()
const start = ref<string | undefined>(undefined)
const week = useWeek(start)
const data = computed(() => week.data.value)
const currentMonday = computed(() => (data.value ? mondayOf(data.value.today) : undefined))
const navModel = computed({
  get: () => data.value?.start ?? start.value ?? '',
  set: (value: string) => (start.value = value),
})
const maxMonday = computed(() => (currentMonday.value ? addWeek(currentMonday.value) : undefined))
const longs = computed(() => tm('ui.weekdays.long') as string[])

function addWeek(monday: string): string {
  const [y, m, d] = monday.split('-').map(Number) as [number, number, number]
  return new Date(Date.UTC(y, m - 1, d + 7)).toISOString().slice(0, 10)
}

function dayTone(day: Day): { tone: string; label: string } | null {
  if (day.met === null) return null
  if (day.met) return { tone: 'success', label: t('studies.week.dayMet') }
  if (day.is_today || day.on > day.today)
    return { tone: 'neutral', label: t('studies.week.dayOpen') }
  const any = day.rows.some((row) => row.done_minutes > 0)
  return any
    ? { tone: 'warning', label: t('studies.week.dayPartial') }
    : { tone: 'danger', label: t('studies.week.dayMissed') }
}

watch(data, (value) => {
  if (value && !start.value) start.value = value.start
})
</script>

<template>
  <PQueryState
    :loading="week.isPending.value"
    :error="week.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div v-if="data" class="week">
      <div class="week__header">
        <PWeekNav
          v-model="navModel"
          :label="t('studies.week.label')"
          :max="maxMonday"
          :current="currentMonday"
        />
        <div class="week__stats">
          <PStatCard
            variant="flat"
            :label="t('studies.week.daysMet')"
            :value="t('studies.week.daysOf', { met: data.days_met, planned: data.days_planned })"
          />
          <PStatCard
            variant="flat"
            :label="t('studies.week.minutes')"
            :value="
              t('studies.week.minutesOf', {
                done: minutes(data.minutes_done),
                planned: minutes(data.minutes_planned),
              })
            "
          />
        </div>
      </div>
      <PCard
        v-for="(day, index) in data.days"
        :key="day.on"
        as="section"
        :title="`${longs[index]}, ${dateShort(day.on)}`"
        :subtitle="day.is_today ? t('studies.week.today') : undefined"
        :heading-level="3"
        variant="flat"
      >
        <template #actions>
          <PBadge v-if="dayTone(day)" :tone="dayTone(day)!.tone">{{ dayTone(day)!.label }}</PBadge>
          <PBadge v-else variant="outline">{{ t('studies.week.noGoalDay') }}</PBadge>
        </template>
        <DayRows v-if="day.rows.length" :rows="day.rows" compact />
      </PCard>
      <PCard v-if="data.by_subject.length" as="section" :title="t('studies.week.bySubject')">
        <PList>
          <PListItem
            v-for="item in data.by_subject"
            :key="item.subject.id"
            :title="item.subject.name"
            :subtitle="
              t('studies.week.minutesOf', {
                done: minutes(item.minutes_done),
                planned: minutes(item.minutes_planned),
              })
            "
            :to="{ name: 'studies.subject', params: { subjectId: item.subject.id } }"
          >
            <template #leading>
              <PTile icon="graduation-cap" :tone="colorTone(item.subject.color)" />
            </template>
          </PListItem>
        </PList>
      </PCard>
      <PText v-else tone="secondary">{{ t('studies.week.empty') }}</PText>
    </div>
  </PQueryState>
</template>

<style scoped>
.week {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.week__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.week__stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
</style>
