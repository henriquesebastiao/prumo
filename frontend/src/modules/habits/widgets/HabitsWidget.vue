<script setup lang="ts">
/** Hábitos on Início (H9): today done over scheduled, the first open habits and the time without. */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { PButton, PCard, PEmptyState, PList, PListItem, PProgress, PText, PTile } from '@/ui'

import type { HabitsSummary } from '../api'
import CheckInDialog from '../forms/CheckInDialog.vue'
import { amount, colorTone, habitIcon } from '../helpers'

const props = defineProps<{ summary?: HabitsSummary }>()
const { t } = useI18n()
const checking = ref(false)
const scheduled = computed(() => props.summary?.scheduled_today ?? 0)
const empty = computed(
  () => !props.summary || (scheduled.value === 0 && props.summary.quit.length === 0),
)
</script>

<template>
  <PCard
    as="article"
    :title="t('habits.nav')"
    icon="list-checks"
    tone="habits"
    :link-label="t('habits.actions.open')"
    :to="{ name: 'habits.home' }"
  >
    <template v-if="summary && !empty">
      <div class="widget__today">
        <PText variant="h2" as="h3">{{
          scheduled
            ? t('habits.widget.today', { done: summary.done_today, scheduled })
            : t('habits.widget.none')
        }}</PText>
        <PProgress
          v-if="scheduled"
          :value="summary.done_today"
          :max="scheduled"
          tone="habits"
          :label="t('habits.titles.today')"
        />
      </div>
      <PList v-if="summary.pending.length || summary.quit.length">
        <PListItem
          v-for="habit in summary.pending"
          :key="habit.id"
          :title="habit.name"
          :subtitle="habit.measure === 'quantity' ? amount(habit, null) : undefined"
          :to="{ name: 'habits.habit', params: { habitId: habit.id } }"
        >
          <template #leading>
            <PTile :icon="habitIcon(habit.icon)" :tone="colorTone(habit.color)" />
          </template>
        </PListItem>
        <PListItem
          v-for="habit in summary.quit"
          :key="habit.id"
          :title="habit.name"
          :subtitle="t('habits.list.clean', { days: t('habits.detail.days', habit.clean_days) })"
          :to="{ name: 'habits.habit', params: { habitId: habit.id } }"
        >
          <template #leading>
            <PTile :icon="habitIcon(habit.icon)" :tone="colorTone(habit.color)" />
          </template>
        </PListItem>
      </PList>
      <PText v-if="summary.pending_more" variant="sm" tone="secondary">{{
        t('habits.widget.more', { n: summary.pending_more })
      }}</PText>
      <div v-if="scheduled" class="widget__actions">
        <PButton variant="tonal" icon="list-checks" @click="checking = true">{{
          t('habits.actions.checkIn')
        }}</PButton>
      </div>
    </template>
    <PEmptyState v-else :title="t('habits.widget.empty')" icon="list-checks" tone="habits" />
  </PCard>
  <CheckInDialog v-model:open="checking" />
</template>

<style scoped>
.widget__today {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.widget__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-3);
}
</style>
