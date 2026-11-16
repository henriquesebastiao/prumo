/** The draft of a frequency in the forms, and its body for the API (H2). */
import type { FrequencyFields, HabitFrequency, Period } from '../api'

export type DraftKind = 'daily' | 'weekdays' | 'month_days' | 'month_weekday' | 'per_period'
export type WeekOfMonth = 1 | 2 | 3 | 4 | -1

export interface FrequencyDraft {
  kind: DraftKind
  weekdays: number[]
  everyNWeeks: number
  monthDays: number[]
  monthLastDay: boolean
  everyNMonths: number
  weekOfMonth: WeekOfMonth
  weekday: number
  times: number
  period: Period
  preferredDay: number | null
}

/** The most `times` of each period; the server checks it too (`habits.times_exceed_period`). */
export const PERIOD_DAYS: Record<Period, number> = { week: 7, fortnight: 14, month: 28 }

export function draftOf(frequency?: HabitFrequency | null): FrequencyDraft {
  const kind = frequency?.kind === 'weekly' ? 'per_period' : (frequency?.kind ?? 'daily')
  return {
    kind,
    weekdays: frequency?.weekdays ?? [0, 1, 2, 3, 4],
    everyNWeeks: frequency?.every_n_weeks ?? 1,
    monthDays: frequency?.month_days ?? [1],
    monthLastDay: frequency?.month_last_day ?? false,
    everyNMonths: frequency?.every_n_months ?? 1,
    weekOfMonth: (frequency?.week_of_month as WeekOfMonth | null | undefined) ?? 1,
    weekday: frequency?.weekday ?? 6,
    times: frequency?.times ?? frequency?.times_per_week ?? 3,
    period: frequency?.period ?? 'week',
    preferredDay: frequency?.preferred_day ?? null,
  }
}

export function fieldsOf(draft: FrequencyDraft): FrequencyFields {
  switch (draft.kind) {
    case 'weekdays':
      return { kind: 'weekdays', weekdays: draft.weekdays, every_n_weeks: draft.everyNWeeks }
    case 'month_days':
      return {
        kind: 'month_days',
        month_days: draft.monthDays,
        month_last_day: draft.monthLastDay,
        every_n_months: draft.everyNMonths,
      }
    case 'month_weekday':
      return {
        kind: 'month_weekday',
        week_of_month: draft.weekOfMonth,
        weekday: draft.weekday,
        every_n_months: draft.everyNMonths,
      }
    case 'per_period':
      return {
        kind: 'per_period',
        times: Math.min(draft.times, PERIOD_DAYS[draft.period]),
        period: draft.period,
        preferred_day: draft.preferredDay,
      }
    default:
      return { kind: 'daily' }
  }
}

export function draftValid(draft: FrequencyDraft): boolean {
  if (draft.kind === 'weekdays') return draft.weekdays.length > 0
  if (draft.kind === 'month_days') return draft.monthDays.length > 0 || draft.monthLastDay
  return true
}
