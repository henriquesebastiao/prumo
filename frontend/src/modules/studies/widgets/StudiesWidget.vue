<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PBadge,
  PButton,
  PCard,
  PEmptyState,
  PList,
  PListItem,
  PProgress,
  PText,
  PTile,
} from '@/ui'

import type { StudiesSummary } from '../api'
import SessionDialog from '../forms/SessionDialog.vue'
import { clock, colorTone, minutes, STATUS_TONE } from '../helpers'

const props = defineProps<{ summary?: StudiesSummary }>()
const { t } = useI18n()
const logging = ref(false)
const blocks = computed(() => props.summary?.blocks_today ?? [])
const planned = computed(() => props.summary?.planned_minutes_today ?? 0)
</script>

<template>
  <PCard
    as="article"
    :title="t('studies.nav')"
    :subtitle="
      summary
        ? t('studies.widget.week', {
            days: t('studies.widget.weekDays', {
              met: summary.week.days_met,
              planned: summary.week.days_planned,
            }),
            minutes: minutes(summary.week.minutes_done),
          })
        : undefined
    "
    icon="graduation-cap"
    tone="studies"
    :link-label="t('studies.actions.open')"
    :to="{ name: 'studies.home' }"
  >
    <template v-if="summary">
      <div class="widget__today">
        <div class="widget__between">
          <PText variant="h2" as="h3">{{ minutes(summary.done_minutes_today) }}</PText>
          <PText variant="sm" tone="secondary" as="span">{{
            planned
              ? t('studies.widget.today', {
                  done: minutes(summary.done_minutes_today),
                  planned: minutes(planned),
                })
              : t('studies.widget.noPlanToday')
          }}</PText>
        </div>
        <PProgress
          v-if="planned"
          :value="Math.min(summary.done_minutes_today, planned)"
          :max="planned"
          tone="studies"
          :label="t('studies.titles.today')"
        />
      </div>
      <PList v-if="blocks.length">
        <PListItem
          v-for="(block, index) in blocks"
          :key="`${block.subject.id}-${index}`"
          :title="block.subject.name"
          :subtitle="
            [
              clock(block.starts_at)
                ? t('studies.today.blockAt', { time: clock(block.starts_at) })
                : '',
              block.goal_minutes ? minutes(block.goal_minutes) : minutes(block.done_minutes),
            ]
              .filter(Boolean)
              .join(' · ')
          "
          :to="{ name: 'studies.subject', params: { subjectId: block.subject.id } }"
        >
          <template #leading>
            <PTile icon="graduation-cap" :tone="colorTone(block.subject.color)" />
          </template>
          <template #trailing>
            <PBadge :tone="STATUS_TONE[block.status]">{{
              t(`studies.status.${block.status}`)
            }}</PBadge>
          </template>
        </PListItem>
      </PList>
      <div class="widget__actions">
        <PButton variant="tonal" icon="add" @click="logging = true">{{
          t('studies.actions.logSession')
        }}</PButton>
      </div>
    </template>
    <PEmptyState v-else :title="t('studies.widget.empty')" icon="graduation-cap" tone="studies" />
  </PCard>
  <SessionDialog v-model:open="logging" />
</template>

<style scoped>
.widget__today {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.widget__between {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.widget__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-3);
}
</style>
