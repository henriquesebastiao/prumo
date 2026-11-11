<script setup lang="ts">
/**
 * A month as a grid of days, Monday first, each day colored by its status (a habit's month). The
 * days come from the API with their status; the component only draws them.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export type CalendarStatus =
  'done' | 'partial' | 'missed' | 'pending' | 'paused' | 'unscheduled' | 'future'

export interface CalendarDay {
  /** `YYYY-MM-DD`. */
  on: string
  status: CalendarStatus
  /** Read after the status, such as "1.250 de 2.000 ml". */
  detail?: string
}

const props = withDefaults(
  defineProps<{
    days: CalendarDay[]
    label: string
    tone?: string
    today?: string
    /** Days up to today become buttons that emit `select` (to mark a past day). */
    selectable?: boolean
  }>(),
  { tone: 'accent', today: undefined, selectable: false },
)
const emit = defineEmits<{ select: [on: string] }>()
const { t, tm } = useI18n()
const shorts = computed(() => tm('ui.weekdays.short') as string[])
const longs = computed(() => tm('ui.weekdays.long') as string[])

function weekday(on: string): number {
  const [y, m, d] = on.split('-').map(Number) as [number, number, number]
  return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7
}

/** Blank cells before the first day, so it falls under its weekday. */
const offset = computed(() => (props.days[0] ? weekday(props.days[0].on) : 0))

function describe(day: CalendarDay): string {
  const number = Number(day.on.slice(8))
  const status = t(`ui.calendar.${day.status}`)
  return [`${longs.value[weekday(day.on)]}, ${number}`, status, day.detail]
    .filter(Boolean)
    .join(' · ')
}
</script>

<template>
  <div class="p-calendar" :data-tone="tone">
    <div class="p-calendar__grid" role="grid" :aria-label="label">
      <div class="p-calendar__row" role="row">
        <span
          v-for="(short, index) in shorts"
          :key="index"
          class="p-calendar__weekday"
          role="columnheader"
          :aria-label="longs[index]"
          >{{ short }}</span
        >
      </div>
      <div class="p-calendar__days" role="row">
        <span v-for="blank in offset" :key="`blank-${blank}`" class="p-calendar__blank" />
        <span v-for="day in days" :key="day.on" role="gridcell" class="p-calendar__cell">
          <component
            :is="selectable && day.status !== 'future' ? 'button' : 'span'"
            :type="selectable && day.status !== 'future' ? 'button' : undefined"
            class="p-calendar__day"
            :class="[
              `p-calendar__day--${day.status}`,
              { 'p-calendar__day--today': day.on === today },
            ]"
            :aria-label="describe(day)"
            :title="describe(day)"
            @click="selectable && day.status !== 'future' && emit('select', day.on)"
            >{{ Number(day.on.slice(8)) }}</component
          >
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.p-calendar__grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-1-5);
}

.p-calendar__row,
.p-calendar__days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-1-5);
}

.p-calendar__weekday {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-align: center;
}

.p-calendar__cell {
  display: grid;
  place-items: center;
}

.p-calendar__day {
  display: grid;
  aspect-ratio: 1;
  max-width: 3rem;
  width: 100%;
  justify-self: center;
  place-items: center;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

button.p-calendar__day {
  font: inherit;
  cursor: pointer;
}

button.p-calendar__day:hover {
  border-color: var(--tone);
}

.p-calendar__day--done {
  background: var(--tone);
  color: var(--color-surface);
  font-weight: var(--weight-semibold);
}

.p-calendar__day--partial {
  border-color: var(--tone);
  background: var(--tone-container);
  color: var(--tone-on-container);
}

.p-calendar__day--missed {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.p-calendar__day--pending {
  border-style: dashed;
  border-color: var(--tone);
  color: var(--color-text);
}

.p-calendar__day--paused {
  background: var(--color-fill);
  color: var(--color-text-muted);
}

.p-calendar__day--unscheduled {
  color: var(--color-text-muted);
}

.p-calendar__day--future {
  color: var(--color-text-muted);
  opacity: 0.6;
}

.p-calendar__day--today {
  outline: 2px solid var(--tone);
  outline-offset: 2px;
}
</style>
