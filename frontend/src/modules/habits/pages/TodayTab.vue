<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { weekdayDate } from '@/lib/format'
import { PCard, PEmptyState, PProgress, PQueryState, PText } from '@/ui'

import { useToday } from '../api'
import TodayList from '../components/TodayList.vue'

const { t } = useI18n()
const query = useToday()
const today = computed(() => query.data.value)
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <PCard v-if="today" as="section" tone="habits" :title="weekdayDate(today.today, false)">
      <template v-if="today.items.length">
        <div class="today__hero">
          <PText variant="number-xl" as="p">{{
            t('habits.today.progress', { done: today.done, scheduled: today.scheduled })
          }}</PText>
          <PProgress
            :value="today.done"
            :max="today.scheduled"
            tone="habits"
            size="lg"
            :label="t('habits.titles.today')"
          />
          <PText v-if="today.done === today.scheduled" tone="success" weight="semibold">{{
            t('habits.today.allDone')
          }}</PText>
        </div>
        <TodayList :items="today.items" :today="today.today" />
      </template>
      <PEmptyState
        v-else
        :title="t('habits.today.empty')"
        :description="t('habits.today.emptyHint')"
        icon="list-checks"
        tone="habits"
      />
    </PCard>
  </PQueryState>
</template>

<style scoped>
.today__hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
</style>
