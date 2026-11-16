<script setup lang="ts">
/**
 * Marks a habit on a day (D47): one tap for a `check`, with "Desfazer" in the toast; a stepper
 * for a `quantity`, sent after a short pause so a run of taps is one write. Every value and every
 * move between the sections of the day comes back from the API.
 */
import { onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { PCheckbox, PStepper, useToast } from '@/ui'

import { useMark, type HabitDayItem } from '../api'

const props = defineProps<{ item: HabitDayItem; on: string }>()
const { t, te } = useI18n()
const toast = useToast()
const mark = useMark()

/** The value being typed with the stepper, sent after a short pause. */
const draft = ref<number | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined
const PAUSE = 500

async function send(value: number | null): Promise<boolean> {
  try {
    await mark.mutateAsync({ id: props.item.habit.id, on: props.on, value })
    return true
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
    return false
  }
}

async function toggle(done: boolean) {
  const sent = await send(done ? 1 : null)
  if (sent && done)
    toast.show({
      title: t('habits.today.marked', { name: props.item.habit.name }),
      action: { label: t('ui.undo'), run: () => void send(null) },
    })
}

function step(): number {
  return Math.max(1, Math.round((props.item.habit.target_value ?? 8) / 8))
}

function change(value: number) {
  draft.value = value
  clearTimeout(timer)
  timer = setTimeout(() => {
    void send(value).then(() => (draft.value = null))
  }, PAUSE)
}

onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <PStepper
    v-if="item.habit.measure === 'quantity'"
    :model-value="draft ?? item.value ?? 0"
    :step="step()"
    :max="1000000"
    :label="t('habits.actions.amount', { name: item.habit.name })"
    @update:model-value="change"
  />
  <PCheckbox
    v-else
    :model-value="item.done"
    :label="
      t(item.done ? 'habits.actions.unmark' : 'habits.actions.mark', { name: item.habit.name })
    "
    @update:model-value="toggle"
  />
</template>
