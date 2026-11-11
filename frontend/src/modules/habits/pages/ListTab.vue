<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { percent } from '@/lib/format'
import { PBadge, PButton, PCard, PEmptyState, PList, PListItem, PQueryState, PTile } from '@/ui'

import { useHabits, type Habit } from '../api'
import { colorTone, frequencyText, habitIcon, streakText } from '../helpers'

const { t } = useI18n()
const showArchived = ref(false)
const query = useHabits(() => (showArchived.value ? 'all' : 'false'))
const habits = computed(() => query.data.value ?? [])
const build = computed(() => habits.value.filter((h) => h.kind === 'build'))
const quit = computed(() => habits.value.filter((h) => h.kind === 'quit'))

function buildSubtitle(habit: Habit): string {
  const parts = [habit.frequency ? frequencyText(t, habit.frequency) : '']
  parts.push(
    habit.rate_percent === null || habit.rate_percent === undefined
      ? t('habits.list.noRate')
      : t('habits.list.rate', { rate: percent(habit.rate_percent) }),
  )
  parts.push(t('habits.list.streak', { streak: streakText(t, habit) }))
  return parts.filter(Boolean).join(' · ')
}

function quitSubtitle(habit: Habit): string {
  const days = habit.clean_days ?? 0
  return [
    t('habits.list.clean', { days: t('habits.detail.days', days) }),
    t('habits.list.relapses', habit.relapses_30d ?? 0),
  ].join(' · ')
}
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div class="list">
      <div class="list__toolbar">
        <PButton variant="ghost" @click="showArchived = !showArchived">{{
          t(showArchived ? 'habits.actions.hideArchived' : 'habits.actions.showArchived')
        }}</PButton>
      </div>
      <PEmptyState
        v-if="!habits.length"
        :title="t('habits.list.empty')"
        :description="t('habits.list.emptyHint')"
        icon="list-checks"
        tone="habits"
        variant="card"
      />
      <PCard v-if="build.length" as="section" :title="t('habits.list.build')" :heading-level="2">
        <PList>
          <PListItem
            v-for="habit in build"
            :key="habit.id"
            :title="habit.name"
            :subtitle="buildSubtitle(habit)"
            :to="{ name: 'habits.habit', params: { habitId: habit.id } }"
          >
            <template #leading>
              <PTile :icon="habitIcon(habit.icon)" :tone="colorTone(habit.color)" />
            </template>
            <template #trailing>
              <PBadge v-if="habit.archived_at" variant="outline">{{
                t('habits.list.archived')
              }}</PBadge>
              <PBadge v-else-if="habit.paused" variant="outline">{{
                t('habits.list.paused')
              }}</PBadge>
            </template>
          </PListItem>
        </PList>
      </PCard>
      <PCard v-if="quit.length" as="section" :title="t('habits.list.quit')" :heading-level="2">
        <PList>
          <PListItem
            v-for="habit in quit"
            :key="habit.id"
            :title="habit.name"
            :subtitle="quitSubtitle(habit)"
            :to="{ name: 'habits.habit', params: { habitId: habit.id } }"
          >
            <template #leading>
              <PTile :icon="habitIcon(habit.icon)" :tone="colorTone(habit.color)" />
            </template>
            <template #trailing>
              <PBadge v-if="habit.archived_at" variant="outline">{{
                t('habits.list.archived')
              }}</PBadge>
            </template>
          </PListItem>
        </PList>
      </PCard>
    </div>
  </PQueryState>
</template>

<style scoped>
.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.list__toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
