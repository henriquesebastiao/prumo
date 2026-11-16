<script setup lang="ts">
/**
 * Hoje (H9): what the day asks, grouped and ordered by the server. The habits with a time in a
 * line with a mark of "now", those without a time in the manual order (draggable, H10), the
 * periods still open, and what was met. Earlier days can be marked late (H3).
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { weekdayDate } from '@/lib/format'
import {
  PButton,
  PCard,
  PDateInput,
  PDivider,
  PEmptyState,
  PIconButton,
  PProgress,
  PQueryState,
  PText,
} from '@/ui'

import { useDay, type HabitsDay } from '../api'
import DayList from '../components/DayList.vue'
import { colorTone, habitIcon } from '../helpers'

const { t } = useI18n()
const picked = ref<string | undefined>(undefined)
const query = useDay(picked)
const day = computed(() => query.data.value)
const showPeriod = ref(false)
const showDone = ref(false)

const isToday = computed(() => !day.value || day.value.on === day.value.today)
const before = computed(() => split(day.value, true))
const after = computed(() => split(day.value, false))
const open = computed(() => (day.value ? day.value.timeline.length + day.value.untimed.length : 0))
const empty = computed(
  () => !!day.value && day.value.scheduled === 0 && day.value.period.length === 0,
)

/** The timeline before and after "now"; on another day, all of it before. */
function split(value: HabitsDay | undefined, past: boolean) {
  if (!value) return []
  const now = value.now
  if (!now) return past ? value.timeline : []
  return value.timeline.filter((item) => (item.habit.time_of_day ?? '') <= now === past)
}

function shift(days: number) {
  if (!day.value) return
  const next = new Date(`${day.value.on}T12:00:00`)
  next.setDate(next.getDate() + days)
  const iso = next.toISOString().slice(0, 10)
  picked.value = iso >= day.value.today ? undefined : iso
}

function pick(value: string) {
  picked.value = !value || (day.value && value >= day.value.today) ? undefined : value
}
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <PCard v-if="day" as="section" tone="habits" :title="weekdayDate(day.on, false)">
      <template #actions>
        <div class="today__nav">
          <PIconButton
            icon="chevron-left"
            :label="t('habits.today.previousDay')"
            variant="ghost"
            @click="shift(-1)"
          />
          <PDateInput
            :model-value="day.on"
            :max="day.today"
            :aria-label="t('habits.today.day')"
            @update:model-value="pick"
          />
          <PIconButton
            icon="chevron-right"
            :label="t('habits.today.nextDay')"
            variant="ghost"
            :disabled="isToday"
            @click="shift(1)"
          />
        </div>
      </template>

      <div class="today">
        <PButton v-if="!isToday" variant="ghost" icon="calendar" @click="picked = undefined">{{
          t('habits.today.backToToday')
        }}</PButton>

        <div v-if="day.scheduled" class="today__hero">
          <PText variant="number-xl" as="p">{{
            t(isToday ? 'habits.today.progress' : 'habits.today.progressPast', {
              done: day.done,
              scheduled: day.scheduled,
            })
          }}</PText>
          <PProgress
            :value="day.done"
            :max="day.scheduled"
            tone="habits"
            size="lg"
            :label="t('habits.titles.today')"
          />
          <PText v-if="!open" tone="success" weight="semibold">{{
            t('habits.today.allDone')
          }}</PText>
        </div>

        <nav
          v-if="day.quit.length"
          class="today__quit"
          :aria-label="t('habits.today.sections.quit')"
        >
          <PButton
            v-for="habit in day.quit"
            :key="habit.id"
            variant="chip"
            :icon="habitIcon(habit.icon)"
            :icon-tone="colorTone(habit.color)"
            :to="{ name: 'habits.habit', params: { habitId: habit.id } }"
            >{{ habit.name }} ·
            {{
              t('habits.list.clean', { days: t('habits.detail.days', habit.clean_days) })
            }}</PButton
          >
        </nav>

        <section v-if="day.timeline.length" class="today__section">
          <PText variant="overline" as="h3">{{ t('habits.today.sections.timeline') }}</PText>
          <DayList v-if="before.length" :items="before" :on="day.on" />
          <PDivider
            v-if="day.now"
            :label="t('habits.today.now', { time: day.now })"
            tone="habits"
          />
          <DayList v-if="after.length" :items="after" :on="day.on" />
        </section>

        <section v-if="day.untimed.length" class="today__section">
          <PText variant="overline" as="h3">{{ t('habits.today.sections.untimed') }}</PText>
          <DayList :items="day.untimed" :on="day.on" sortable />
        </section>

        <section v-if="day.period.length" class="today__section">
          <PButton
            variant="ghost"
            :icon-right="showPeriod ? 'chevron-down' : 'chevron-right'"
            :aria-expanded="showPeriod"
            @click="showPeriod = !showPeriod"
            >{{ t('habits.today.sections.period', { n: day.period.length }) }}</PButton
          >
          <DayList v-if="showPeriod" :items="day.period" :on="day.on" />
        </section>

        <section v-if="day.done_items.length" class="today__section">
          <PButton
            variant="ghost"
            :icon-right="showDone ? 'chevron-down' : 'chevron-right'"
            :aria-expanded="showDone"
            @click="showDone = !showDone"
            >{{
              t(isToday ? 'habits.today.sections.done' : 'habits.today.sections.donePast', {
                n: day.done_items.length,
              })
            }}</PButton
          >
          <DayList v-if="showDone" :items="day.done_items" :on="day.on" />
        </section>

        <PEmptyState
          v-if="empty"
          :title="t('habits.today.empty')"
          :description="t('habits.today.emptyHint')"
          icon="list-checks"
          tone="habits"
        />
      </div>
    </PCard>
  </PQueryState>
</template>

<style scoped>
.today {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.today__nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.today__hero,
.today__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.today__section > :first-child {
  align-self: flex-start;
}

.today__quit {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
