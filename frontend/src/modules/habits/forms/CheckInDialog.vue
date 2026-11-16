<script setup lang="ts">
/**
 * "Marcar hábitos" (quick action, shortcut H in the N menu): every habit of today, the periods
 * still open included, with a search by name that ignores accents and case.
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { PButton, PDialog, PEmptyState, PQueryState, PSearchField, PText } from '@/ui'

import { useDay } from '../api'
import DayList from '../components/DayList.vue'
import { searchable } from '../helpers'

const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const query = useDay()
const day = computed(() => query.data.value)
const search = ref('')

watch(open, (value) => {
  if (value) search.value = ''
})

const items = computed(() => {
  const value = day.value
  if (!value) return []
  const all = [...value.timeline, ...value.untimed, ...value.period, ...value.done_items]
  const wanted = searchable(search.value)
  return wanted ? all.filter((item) => searchable(item.habit.name).includes(wanted)) : all
})
const hasAny = computed(
  () =>
    !!day.value &&
    day.value.timeline.length +
      day.value.untimed.length +
      day.value.period.length +
      day.value.done_items.length >
      0,
)
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('habits.form.titles.checkIn')"
    icon="list-checks"
    tone="habits"
  >
    <PQueryState
      :loading="query.isPending.value"
      :error="query.error.value"
      :error-title="t('ui.loadFailed')"
    >
      <div v-if="day && hasAny" class="check-in">
        <PSearchField v-model="search" :placeholder="t('habits.today.searchPlaceholder')" />
        <DayList v-if="items.length" :items="items" :on="day.on" />
        <PText v-else tone="secondary">{{ t('habits.today.noResults') }}</PText>
      </div>
      <PEmptyState
        v-else
        :title="t('habits.today.empty')"
        :description="t('habits.today.emptyHint')"
        icon="list-checks"
        tone="habits"
      />
    </PQueryState>
    <template #footer>
      <PButton variant="primary" @click="open = false">{{ t('ui.close') }}</PButton>
    </template>
  </PDialog>
</template>

<style scoped>
.check-in {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>
