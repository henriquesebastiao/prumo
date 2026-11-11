<script setup lang="ts">
/** The subjects of one day: goal, minutes done and status (E4), with the blocks' times. */
import { useI18n } from 'vue-i18n'

import { PBadge, PList, PListItem, PProgress, PTile } from '@/ui'

import type { DayRow } from '../api'
import { clock, colorTone, minutes, STATUS_TONE } from '../helpers'

defineProps<{ rows: DayRow[]; compact?: boolean }>()
const { t } = useI18n()

function subtitle(row: DayRow): string {
  const times = row.blocks.map((b) => clock(b.starts_at)).filter(Boolean)
  const when = times.length ? t('studies.today.blockAt', { time: times.join(', ') }) + ' · ' : ''
  const goal = row.goal_minutes
    ? t('studies.today.goal', { minutes: minutes(row.goal_minutes) })
    : t('studies.today.noGoal')
  const done = row.done_minutes
    ? t('studies.today.done', { minutes: minutes(row.done_minutes) })
    : t('studies.today.nothingYet')
  return `${when}${goal} · ${done}`
}
</script>

<template>
  <PList>
    <PListItem
      v-for="row in rows"
      :key="row.subject.id"
      :title="row.subject.name"
      :subtitle="subtitle(row)"
      :to="{ name: 'studies.subject', params: { subjectId: row.subject.id } }"
    >
      <template #leading>
        <PTile
          icon="graduation-cap"
          :tone="colorTone(row.subject.color)"
          :size="compact ? 'md' : 'lg'"
        />
      </template>
      <template #trailing>
        <span class="rows__trailing">
          <PProgress
            v-if="row.goal_minutes"
            class="rows__bar"
            :value="Math.min(row.done_minutes, row.goal_minutes)"
            :max="row.goal_minutes"
            tone="studies"
            size="sm"
            :label="row.subject.name"
          />
          <PBadge :tone="STATUS_TONE[row.status]">{{ t(`studies.status.${row.status}`) }}</PBadge>
        </span>
      </template>
    </PListItem>
  </PList>
</template>

<style scoped>
.rows__trailing {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.rows__bar {
  width: 72px;
}

@media (width < 700px) {
  .rows__bar {
    display: none;
  }
}
</style>
