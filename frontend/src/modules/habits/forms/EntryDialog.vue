<script setup lang="ts">
/** The value of a `quantity` habit on one day (a past day from the calendar, or today). */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date } from '@/lib/format'
import { PAlert, PButton, PDialog, PField, PNumberInput, useToast } from '@/ui'

import { useMark, type Habit } from '../api'

const props = defineProps<{ habit: Habit; on: string; value: number | null }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const mark = useMark()
const saving = mark.isPending

const amount = ref<number | null>(null)
const failure = ref<string | null>(null)

watch(
  open,
  (value) => {
    if (!value) return
    failure.value = null
    amount.value = props.value
  },
  { immediate: true },
)

async function send(value: number | null) {
  failure.value = null
  try {
    await mark.mutateAsync({ id: props.habit.id, on: props.on, value })
    open.value = false
  } catch (error) {
    failure.value = errorMessage(error, { t, te })
    toast.show({ title: failure.value, tone: 'danger' })
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('habits.form.titles.entry', { name: habit.name })"
    icon="list-checks"
    tone="habits"
    size="s"
  >
    <form id="entry-form" class="form" novalidate @submit.prevent="send(amount ?? 0)">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('habits.form.value', { day: date(on) })">
        <PNumberInput v-model="amount" :suffix="habit.unit ?? undefined" />
      </PField>
    </form>
    <template #footer>
      <PButton v-if="value !== null" variant="ghost" @click="send(null)">{{
        t('habits.actions.clear')
      }}</PButton>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton type="submit" form="entry-form" variant="primary" :loading="saving">{{
        t('habits.actions.save')
      }}</PButton>
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
