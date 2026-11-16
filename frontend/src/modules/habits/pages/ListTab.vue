<script setup lang="ts">
/**
 * Hábitos, the management list: search by name (accents and case ignored), filters by kind,
 * cadence and archived, in the order of the server (H10). The habits without a time are dragged
 * into a new manual order; those with a time show it in place of the handle.
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { percent } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PEmptyState,
  PList,
  PListItem,
  PQueryState,
  PSearchField,
  PSelect,
  PSortableList,
  PText,
  PTile,
  useToast,
} from '@/ui'

import { useHabits, useReorder, type Cadence, type Habit } from '../api'
import { colorTone, dueText, frequencyText, habitIcon, searchable, streakText } from '../helpers'

const { t, te } = useI18n()
const toast = useToast()
const reorder = useReorder()
const showArchived = ref(false)
const search = ref('')
const kind = ref<'all' | 'build' | 'quit'>('all')
const cadence = ref<'all' | Cadence>('all')
const query = useHabits(() => (showArchived.value ? 'all' : 'false'))
const habits = computed(() => query.data.value ?? [])

const filtering = computed(
  () => Boolean(searchable(search.value)) || kind.value !== 'all' || cadence.value !== 'all',
)
const shown = computed(() => {
  const wanted = searchable(search.value)
  return habits.value.filter(
    (habit) =>
      (!wanted || searchable(habit.name).includes(wanted)) &&
      (kind.value === 'all' || habit.kind === kind.value) &&
      (cadence.value === 'all' || habit.frequency?.cadence === cadence.value),
  )
})
const timed = computed(() => shown.value.filter((h) => h.kind === 'build' && h.time_of_day))
const untimed = ref<Habit[]>([])
watch(
  shown,
  (value) => (untimed.value = value.filter((h) => h.kind === 'build' && !h.time_of_day)),
  { immediate: true },
)
const quit = computed(() => shown.value.filter((h) => h.kind === 'quit'))
const sortable = computed(() => !filtering.value && untimed.value.length > 1)

const sorted = computed({
  get: () => untimed.value,
  set: (items: Habit[]) => {
    untimed.value = items
    reorder
      .mutateAsync(items.map((habit) => habit.id))
      .catch((error: unknown) =>
        toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' }),
      )
  },
})

const kindOptions = computed(() => [
  { value: 'all' as const, label: t('habits.list.filters.allKinds') },
  { value: 'build' as const, label: t('habits.kinds.build') },
  { value: 'quit' as const, label: t('habits.kinds.quit') },
])
const cadenceOptions = computed(() => [
  { value: 'all' as const, label: t('habits.list.filters.allCadences') },
  ...(['daily', 'weekly', 'fortnightly', 'monthly', 'longer'] as const).map((value) => ({
    value,
    label: t(`habits.frequency.cadences.${value}`),
  })),
])

function buildSubtitle(habit: Habit): string {
  const parts = [habit.frequency ? frequencyText(t, habit.frequency) : '']
  parts.push(
    habit.rate_percent === null || habit.rate_percent === undefined
      ? t('habits.list.noRate')
      : t('habits.list.rate', { rate: percent(habit.rate_percent) }),
  )
  parts.push(t('habits.list.streak', { streak: streakText(t, habit) }))
  if (habit.next_due && !habit.archived_at)
    parts.push(t('habits.list.next', { date: dueText(t, habit.next_due) }))
  return parts.filter(Boolean).join(' · ')
}

function quitSubtitle(habit: Habit): string {
  const days = habit.clean_days ?? 0
  return [
    t('habits.list.clean', { days: t('habits.detail.days', days) }),
    t('habits.list.relapses', habit.relapses_30d ?? 0),
  ].join(' · ')
}

function link(habit: Habit) {
  return { name: 'habits.habit', params: { habitId: habit.id } }
}
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div class="list">
      <div class="list__toolbar" role="search">
        <PSearchField v-model="search" :placeholder="t('habits.list.search')" />
        <div class="list__filters">
          <PSelect
            v-model="kind"
            :options="kindOptions"
            variant="filter"
            :aria-label="t('habits.list.filters.kind')"
          />
          <PSelect
            v-model="cadence"
            :options="cadenceOptions"
            variant="filter"
            :aria-label="t('habits.list.filters.cadence')"
          />
          <PButton variant="ghost" @click="showArchived = !showArchived">{{
            t(showArchived ? 'habits.actions.hideArchived' : 'habits.actions.showArchived')
          }}</PButton>
        </div>
      </div>
      <PEmptyState
        v-if="!habits.length"
        :title="t('habits.list.empty')"
        :description="t('habits.list.emptyHint')"
        icon="list-checks"
        tone="habits"
        variant="card"
      />
      <PText v-else-if="!shown.length" tone="secondary">{{ t('habits.list.noMatch') }}</PText>
      <PCard
        v-if="timed.length || untimed.length"
        as="section"
        :title="t('habits.list.build')"
        :heading-level="2"
      >
        <PList v-if="timed.length">
          <PListItem
            v-for="habit in timed"
            :key="habit.id"
            :title="habit.name"
            :subtitle="buildSubtitle(habit)"
            :to="link(habit)"
          >
            <template #leading>
              <PText variant="strong" as="span" class="list__time">{{ habit.time_of_day }}</PText>
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
        <template v-if="untimed.length">
          <PSortableList
            v-if="sortable"
            v-model="sorted"
            :item-key="(habit: Habit) => habit.id"
            :item-label="(habit: Habit) => habit.name"
            :label="t('habits.list.reorder')"
          >
            <template #default="{ item }">
              <PList class="list__sortable-item">
                <PListItem :title="item.name" :subtitle="buildSubtitle(item)" :to="link(item)">
                  <template #leading>
                    <PTile :icon="habitIcon(item.icon)" :tone="colorTone(item.color)" />
                  </template>
                  <template #trailing>
                    <PBadge v-if="item.archived_at" variant="outline">{{
                      t('habits.list.archived')
                    }}</PBadge>
                    <PBadge v-else-if="item.paused" variant="outline">{{
                      t('habits.list.paused')
                    }}</PBadge>
                  </template>
                </PListItem>
              </PList>
            </template>
          </PSortableList>
          <PList v-else>
            <PListItem
              v-for="habit in untimed"
              :key="habit.id"
              :title="habit.name"
              :subtitle="buildSubtitle(habit)"
              :to="link(habit)"
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
          <PText v-if="sortable" variant="sm" tone="secondary">{{
            t('habits.list.reorderHint')
          }}</PText>
        </template>
      </PCard>
      <PCard v-if="quit.length" as="section" :title="t('habits.list.quit')" :heading-level="2">
        <PList>
          <PListItem
            v-for="habit in quit"
            :key="habit.id"
            :title="habit.name"
            :subtitle="quitSubtitle(habit)"
            :to="link(habit)"
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
  flex-direction: column;
  gap: var(--space-2);
}

.list__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.list__filters > * {
  width: auto;
  flex: none;
}

.list__time {
  min-width: 3rem;
}

.list__sortable-item {
  min-width: 0;
  flex: 1;
}
</style>
