<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { weekdayDate } from '@/lib/format'
import { PButton, PCard, PEmptyState, PProgress, PQueryState, PStatCard, PText } from '@/ui'

import { useDay, useWeek } from '../api'
import DayRows from '../components/DayRows.vue'
import SessionDialog from '../forms/SessionDialog.vue'
import { minutes } from '../helpers'

const { t } = useI18n()
const day = useDay()
const week = useWeek()
const today = computed(() => day.data.value)
const logging = ref(false)
</script>

<template>
  <PQueryState
    :loading="day.isPending.value"
    :error="day.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div v-if="today" class="today">
      <PCard as="section" tone="studies" :title="weekdayDate(today.on, false)">
        <div class="today__hero">
          <div class="today__minutes">
            <PText variant="number-xl" as="p">{{ minutes(today.done_minutes) }}</PText>
            <PText tone="secondary">{{
              t('studies.today.progress', {
                done: minutes(today.done_minutes),
                planned: minutes(today.planned_minutes),
              })
            }}</PText>
          </div>
          <PProgress
            v-if="today.planned_minutes"
            :value="Math.min(today.done_minutes, today.planned_minutes)"
            :max="today.planned_minutes"
            tone="studies"
            size="lg"
            :label="t('studies.titles.today')"
          />
          <PText v-if="today.met" tone="success" weight="semibold">{{
            t('studies.today.dayMet')
          }}</PText>
        </div>
        <DayRows v-if="today.rows.length" :rows="today.rows" />
        <PEmptyState
          v-else
          :title="t('studies.today.noPlan')"
          :description="t('studies.today.noPlanHint')"
          icon="calendar"
          tone="studies"
        />
        <template #actions>
          <PButton variant="tonal" icon="add" @click="logging = true">{{
            t('studies.actions.logSession')
          }}</PButton>
        </template>
      </PCard>
      <div v-if="week.data.value" class="today__week">
        <PStatCard
          :label="t('studies.week.daysMet')"
          :value="
            t('studies.week.daysOf', {
              met: week.data.value.days_met,
              planned: week.data.value.days_planned,
            })
          "
          :caption="t('ui.thisWeek')"
        />
        <PStatCard
          :label="t('studies.week.minutes')"
          :value="
            t('studies.week.minutesOf', {
              done: minutes(week.data.value.minutes_done),
              planned: minutes(week.data.value.minutes_planned),
            })
          "
          :caption="t('ui.thisWeek')"
        />
      </div>
    </div>
  </PQueryState>
  <SessionDialog v-model:open="logging" />
</template>

<style scoped>
.today {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.today__hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.today__minutes {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}

.today__week {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
}
</style>
