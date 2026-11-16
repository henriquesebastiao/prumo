<script setup lang="ts">
/**
 * Habits of a day (H9) as the server grouped them, each with its control. `sortable` lets the
 * habits without a time be dragged into a new manual order (H10).
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { PBadge, PList, PListItem, PSortableList, PText, PTile, useToast } from '@/ui'

import { useReorder, type HabitDayItem } from '../api'
import { amount, colorTone, habitIcon, periodText } from '../helpers'
import DayControl from './DayControl.vue'

const props = defineProps<{ items: HabitDayItem[]; on: string; sortable?: boolean }>()
const { t, te } = useI18n()
const toast = useToast()
const reorder = useReorder()

const ordered = ref<HabitDayItem[]>([])
watch(
  () => props.items,
  (items) => (ordered.value = [...items]),
  { immediate: true },
)
const sorted = computed({
  get: () => ordered.value,
  set: (items: HabitDayItem[]) => {
    ordered.value = items
    reorder
      .mutateAsync(items.map((item) => item.habit.id))
      .catch((error: unknown) =>
        toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' }),
      )
  },
})

function subtitle(item: HabitDayItem): string {
  const parts: string[] = []
  if (item.habit.time_of_day) parts.push(item.habit.time_of_day)
  if (item.habit.measure === 'quantity') parts.push(amount(item.habit, item.value))
  if (item.period && !item.done) parts.push(periodText(t, item.period))
  if (item.promoted === 'preferred_day') parts.push(t('habits.today.preferredDay'))
  if (item.promoted === 'due_soon') parts.push(t('habits.today.dueSoon', item.due_in_days ?? 0))
  return parts.join(' · ')
}
</script>

<template>
  <PSortableList
    v-if="sortable && ordered.length > 1"
    v-model="sorted"
    :item-key="(item: HabitDayItem) => item.habit.id"
    :item-label="(item: HabitDayItem) => item.habit.name"
    :label="t('habits.today.reorder')"
  >
    <template #default="{ item }">
      <div class="day__row">
        <PTile :icon="habitIcon(item.habit.icon)" :tone="colorTone(item.habit.color)" />
        <div class="day__body">
          <PText weight="semibold">{{ item.habit.name }}</PText>
          <PText v-if="subtitle(item)" variant="sm" tone="secondary">{{ subtitle(item) }}</PText>
        </div>
        <span class="day__control"><DayControl :item="item" :on="on" /></span>
      </div>
    </template>
  </PSortableList>
  <PList v-else>
    <PListItem
      v-for="item in ordered"
      :key="item.habit.id"
      :title="item.habit.name"
      :subtitle="subtitle(item) || undefined"
    >
      <template #leading>
        <PTile :icon="habitIcon(item.habit.icon)" :tone="colorTone(item.habit.color)" />
      </template>
      <template #trailing>
        <PBadge v-if="item.late" tone="warning">{{ t('habits.today.late') }}</PBadge>
        <PBadge v-else-if="item.period && !item.done && item.settled" tone="success">{{
          t('habits.today.periodDone')
        }}</PBadge>
        <DayControl :item="item" :on="on" />
      </template>
    </PListItem>
  </PList>
</template>

<style scoped>
.day__row {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: var(--space-3);
}

.day__control {
  display: inline-flex;
  flex: none;
  align-items: center;
}

.day__body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}
</style>
