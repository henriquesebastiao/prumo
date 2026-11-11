<script setup lang="ts">
/**
 * The habits of today (H2): a tap marks a `check`, a stepper sets a `quantity`, a `weekly` shows
 * its week. Every value comes from the API; a change is sent as the day's entry (D47).
 */
import { onBeforeUnmount, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { PBadge, PCheckbox, PList, PListItem, PStepper, PTile, useToast } from '@/ui'

import { useMark, type HabitTodayItem } from '../api'
import { amount, colorTone, habitIcon } from '../helpers'

const props = defineProps<{ items: HabitTodayItem[]; today: string }>()
const { t, te } = useI18n()
const toast = useToast()
const mark = useMark()

/** Values being typed with the stepper, sent after a short pause. */
const drafts = reactive<Record<string, number>>({})
const timers = new Map<string, ReturnType<typeof setTimeout>>()
const PAUSE = 500

async function send(id: string, value: number | null) {
  try {
    await mark.mutateAsync({ id, on: props.today, value })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

function toggle(item: HabitTodayItem, done: boolean) {
  void send(item.habit.id, done ? 1 : null)
}

function step(item: HabitTodayItem): number {
  return Math.max(1, Math.round((item.habit.target_value ?? 8) / 8))
}

function change(item: HabitTodayItem, value: number) {
  const id = item.habit.id
  drafts[id] = value
  clearTimeout(timers.get(id))
  timers.set(
    id,
    setTimeout(() => {
      timers.delete(id)
      void send(id, value).then(() => delete drafts[id])
    }, PAUSE),
  )
}

function subtitle(item: HabitTodayItem): string {
  const parts = []
  if (item.habit.measure === 'quantity')
    parts.push(amount(item.habit, drafts[item.habit.id] ?? item.value))
  if (item.week)
    parts.push(t('habits.today.week', { done: item.week.done, target: item.week.target }))
  return parts.join(' · ')
}

onBeforeUnmount(() => timers.forEach((timer) => clearTimeout(timer)))
</script>

<template>
  <PList>
    <PListItem
      v-for="item in items"
      :key="item.habit.id"
      :title="item.habit.name"
      :subtitle="subtitle(item) || undefined"
    >
      <template #leading>
        <PTile :icon="habitIcon(item.habit.icon)" :tone="colorTone(item.habit.color)" />
      </template>
      <template #trailing>
        <div class="today__control">
          <PBadge v-if="item.week && !item.done && item.settled" tone="success">{{
            t('habits.today.weekDone')
          }}</PBadge>
          <PStepper
            v-if="item.habit.measure === 'quantity'"
            :model-value="drafts[item.habit.id] ?? item.value ?? 0"
            :step="step(item)"
            :max="1000000"
            :label="t('habits.actions.amount', { name: item.habit.name })"
            @update:model-value="(value: number) => change(item, value)"
          />
          <PCheckbox
            v-else
            :model-value="item.done"
            :label="
              t(item.done ? 'habits.actions.unmark' : 'habits.actions.mark', {
                name: item.habit.name,
              })
            "
            @update:model-value="(done: boolean) => toggle(item, done)"
          />
        </div>
      </template>
    </PListItem>
  </PList>
</template>

<style scoped>
.today__control {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
</style>
