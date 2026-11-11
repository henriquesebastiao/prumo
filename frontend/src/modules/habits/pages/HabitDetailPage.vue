<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { errorMessage } from '@/lib/errors'
import { date, dateTime, integer, percent } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PConfirmDialog,
  PIconButton,
  PList,
  PListItem,
  PMenu,
  PMonthCalendar,
  PMonthNav,
  PPageHeader,
  PQueryState,
  PStatCard,
  PText,
  useToast,
  type CalendarDay,
  type MenuEntry,
} from '@/ui'

import {
  useArchiveHabit,
  useCalendar,
  useDeleteFrequency,
  useDeleteHabit,
  useDeletePause,
  useDeleteRelapse,
  useHabit,
  useMark,
  useSavePause,
  type HabitFrequency,
} from '../api'
import EntryDialog from '../forms/EntryDialog.vue'
import FrequencyDialog from '../forms/FrequencyDialog.vue'
import HabitDialog from '../forms/HabitDialog.vue'
import PauseDialog from '../forms/PauseDialog.vue'
import RelapseDialog from '../forms/RelapseDialog.vue'
import { amount, frequencyText, monthOf, streakText } from '../helpers'

const props = defineProps<{ habitId: string }>()
const { t, te } = useI18n()
const toast = useToast()
const router = useRouter()
const query = useHabit(() => props.habitId)
const habit = computed(() => query.data.value)
const build = computed(() => habit.value?.kind === 'build')

const month = ref<string>()
const calendar = useCalendar(() => props.habitId, month, build)
const today = computed(() => calendar.data.value?.today)
watch(
  () => calendar.data.value?.month,
  (value) => {
    if (value && !month.value) month.value = value
  },
)
const monthModel = computed({
  get: () => month.value ?? calendar.data.value?.month ?? '',
  set: (value: string) => (month.value = value),
})

const archive = useArchiveHabit()
const remove = useDeleteHabit()
const mark = useMark()
const removeFrequency = useDeleteFrequency()
const savePause = useSavePause()
const removePause = useDeletePause()
const removeRelapse = useDeleteRelapse()

const editing = ref(false)
const confirming = ref(false)
const frequencyOpen = ref(false)
const editingFrequency = ref<HabitFrequency>()
const pauseOpen = ref(false)
const relapseOpen = ref(false)
const entryDay = ref<string>()
const entryOpen = ref(false)

async function run(action: () => Promise<unknown>, success?: string) {
  try {
    await action()
    if (success) toast.show({ title: success })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

const menu = computed<MenuEntry[]>(() => {
  const archived = Boolean(habit.value?.archived_at)
  return [
    { label: t('habits.actions.edit'), icon: 'edit', onSelect: () => (editing.value = true) },
    {
      label: t(archived ? 'habits.actions.unarchive' : 'habits.actions.archive'),
      icon: 'archive',
      onSelect: () => run(() => archive.mutateAsync({ id: props.habitId, archived: !archived })),
    },
    { type: 'separator' },
    {
      label: t('habits.actions.delete'),
      icon: 'trash',
      tone: 'danger',
      onSelect: () => (confirming.value = true),
    },
  ]
})

async function destroy() {
  confirming.value = false
  await run(async () => {
    await remove.mutateAsync(props.habitId)
    await router.push({ name: 'habits.list' })
  }, t('habits.detail.deleted'))
}

const days = computed<CalendarDay[]>(() => {
  const current = habit.value
  return (calendar.data.value?.days ?? []).map((day) => ({
    on: day.on,
    status: day.status,
    detail:
      current?.measure === 'quantity' && day.value !== null && day.value !== undefined
        ? amount(current, day.value)
        : undefined,
  }))
})

/** A day of the calendar: a `check` toggles, a `quantity` asks its value. */
function select(on: string) {
  const current = habit.value
  if (!current) return
  if (current.measure === 'quantity') {
    entryDay.value = on
    entryOpen.value = true
    return
  }
  const day = calendar.data.value?.days.find((d) => d.on === on)
  const done = day?.status === 'done'
  void run(() => mark.mutateAsync({ id: props.habitId, on, value: done ? null : 1 }))
}

function frequencyLabel(frequency: HabitFrequency): string {
  if (frequency.state === 'current')
    return t('habits.frequency.current', { date: date(frequency.valid_from) })
  if (frequency.state === 'future')
    return t('habits.frequency.future', { date: date(frequency.valid_from) })
  return t('habits.frequency.past', {
    from: date(frequency.valid_from),
    until: frequency.valid_until ? date(frequency.valid_until) : '',
  })
}

function openFrequency(frequency?: HabitFrequency) {
  editingFrequency.value = frequency
  frequencyOpen.value = true
}

const rateHint = computed(() =>
  habit.value?.streak_unit === 'week'
    ? t('habits.detail.rateHintWeeks')
    : t('habits.detail.rateHint'),
)
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div v-if="habit" class="habit">
      <PPageHeader
        :overline="
          build && habit.frequency
            ? frequencyText(t, habit.frequency)
            : t(`habits.list.${habit.kind}`)
        "
        :title="habit.name"
        :back="{ label: t('habits.detail.back'), to: { name: 'habits.list' } }"
      >
        <PBadge v-if="habit.archived_at" variant="outline">{{ t('habits.list.archived') }}</PBadge>
        <PButton v-if="!build" variant="primary" icon="add" @click="relapseOpen = true">{{
          t('habits.actions.logRelapse')
        }}</PButton>
        <PMenu :items="menu">
          <template #trigger>
            <PIconButton icon="more" :label="t('habits.actions.more')" />
          </template>
        </PMenu>
      </PPageHeader>

      <template v-if="build">
        <div class="habit__stats">
          <PStatCard
            :label="t('habits.detail.rate')"
            :value="habit.rate_percent === null ? '—' : percent(habit.rate_percent ?? 0)"
            :caption="rateHint"
          />
          <PStatCard :label="t('habits.detail.streak')" :value="streakText(t, habit)" />
          <PStatCard
            :label="t('habits.detail.best')"
            :value="
              streakText(t, { current_streak: habit.best_streak, streak_unit: habit.streak_unit })
            "
          />
          <PStatCard
            v-if="habit.week"
            :label="t('habits.detail.week')"
            :value="t('habits.today.week', { done: habit.week.done, target: habit.week.target })"
          />
        </div>

        <PCard as="section" :title="t('habits.detail.calendar')" :heading-level="2" tone="habits">
          <template #actions>
            <PMonthNav
              v-if="monthModel"
              v-model="monthModel"
              :label="t('habits.detail.calendar')"
              :max="today ? monthOf(today) : undefined"
            />
          </template>
          <PMonthCalendar
            :days="days"
            :label="t('habits.detail.calendar')"
            tone="habits"
            :today="today"
            selectable
            @select="select"
          />
        </PCard>

        <div class="habit__columns">
          <PCard as="section" :title="t('habits.detail.frequencies')" :heading-level="2">
            <template #actions>
              <PButton variant="tonal" icon="add" @click="openFrequency()">{{
                t('habits.actions.changeFrequency')
              }}</PButton>
            </template>
            <PList>
              <PListItem
                v-for="frequency in habit.frequencies"
                :key="frequency.id"
                :title="frequencyText(t, frequency)"
                :subtitle="frequencyLabel(frequency)"
              >
                <template #trailing>
                  <template v-if="frequency.state === 'future'">
                    <PIconButton
                      icon="edit"
                      :label="t('habits.actions.editVersion')"
                      variant="ghost"
                      @click="openFrequency(frequency)"
                    />
                    <PIconButton
                      icon="trash"
                      :label="t('habits.actions.delete')"
                      variant="ghost"
                      @click="
                        run(
                          () => removeFrequency.mutateAsync(frequency.id),
                          t('habits.frequency.deleted'),
                        )
                      "
                    />
                  </template>
                </template>
              </PListItem>
            </PList>
            <PText variant="sm" tone="secondary">{{ t('habits.frequency.locked') }}</PText>
          </PCard>

          <PCard as="section" :title="t('habits.detail.pauses')" :heading-level="2">
            <template #actions>
              <PButton variant="tonal" icon="pause" @click="pauseOpen = true">{{
                t('habits.actions.addPause')
              }}</PButton>
            </template>
            <PList v-if="habit.pauses.length">
              <PListItem
                v-for="pause in habit.pauses"
                :key="pause.id"
                :title="
                  pause.ends_on
                    ? t('habits.detail.pauseRange', {
                        from: date(pause.starts_on),
                        until: date(pause.ends_on),
                      })
                    : t('habits.detail.pauseOpen', { date: date(pause.starts_on) })
                "
              >
                <template #trailing>
                  <PButton
                    v-if="!pause.ends_on && today"
                    variant="ghost"
                    @click="
                      run(() =>
                        savePause.mutateAsync({
                          habitId,
                          id: pause.id,
                          body: { starts_on: pause.starts_on, ends_on: today },
                        }),
                      )
                    "
                    >{{ t('habits.actions.endPause') }}</PButton
                  >
                  <PIconButton
                    icon="trash"
                    :label="t('habits.detail.deletePause')"
                    variant="ghost"
                    @click="run(() => removePause.mutateAsync(pause.id))"
                  />
                </template>
              </PListItem>
            </PList>
            <PText v-else tone="secondary">{{ t('habits.detail.noPauses') }}</PText>
          </PCard>
        </div>
      </template>

      <template v-else>
        <div class="habit__stats">
          <PStatCard
            :label="t('habits.detail.cleanDays')"
            :value="t('habits.detail.days', habit.clean_days ?? 0)"
            :caption="
              habit.clean_since
                ? t('habits.detail.cleanSince', { date: dateTime(habit.clean_since) })
                : undefined
            "
          />
          <PStatCard
            :label="t('habits.detail.bestClean')"
            :value="t('habits.detail.days', habit.best_clean_days ?? 0)"
          />
          <PStatCard
            :label="t('habits.detail.relapses30')"
            :value="integer(habit.relapses_30d ?? 0)"
          />
        </div>
        <PCard as="section" :title="t('habits.detail.relapses')" :heading-level="2">
          <PList v-if="habit.relapses.length">
            <PListItem
              v-for="relapse in habit.relapses"
              :key="relapse.id"
              :title="dateTime(relapse.occurred_at)"
              :subtitle="relapse.note ?? undefined"
            >
              <template #trailing>
                <PIconButton
                  icon="trash"
                  :label="t('habits.detail.deleteRelapse')"
                  variant="ghost"
                  @click="run(() => removeRelapse.mutateAsync(relapse.id))"
                />
              </template>
            </PListItem>
          </PList>
          <PText v-else tone="secondary">{{ t('habits.detail.noRelapses') }}</PText>
        </PCard>
      </template>
      <PText variant="sm" tone="secondary">{{
        t('habits.detail.started', { date: date(habit.started_on) })
      }}</PText>
    </div>
  </PQueryState>
  <HabitDialog v-if="habit" v-model:open="editing" :habit="habit" />
  <FrequencyDialog
    v-if="habit"
    v-model:open="frequencyOpen"
    :habit-id="habitId"
    :frequency="editingFrequency"
    :today="today"
  />
  <PauseDialog v-if="habit" v-model:open="pauseOpen" :habit-id="habitId" :today="today" />
  <RelapseDialog v-if="habit" v-model:open="relapseOpen" :habit-id="habitId" />
  <EntryDialog
    v-if="habit && entryDay"
    v-model:open="entryOpen"
    :habit="habit"
    :on="entryDay"
    :value="calendar.data.value?.days.find((d) => d.on === entryDay)?.value ?? null"
  />
  <PConfirmDialog
    v-if="habit"
    v-model:open="confirming"
    :title="t('habits.detail.deleteTitle')"
    :description="t('habits.detail.deleteBody', { name: habit.name })"
    :confirm-label="t('habits.actions.delete')"
    @confirm="destroy"
  />
</template>

<style scoped>
.habit {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.habit__stats {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr));
}

.habit__columns {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
}
</style>
