/** Presentation helpers of the habits module. */
import type { Translate } from '@/app/registry'
import { dateShort, integer } from '@/lib/format'
import type { IconName, Tone } from '@/ui'

import type { Habit, HabitFrequency, HabitPeriod, HabitRef } from './api'

const PICKER_COLORS = ['amber', 'orange', 'green', 'blue', 'violet', 'pink', 'cyan', 'gray']
const ALL_COLORS = [
  'green',
  'teal',
  'cyan',
  'blue',
  'indigo',
  'violet',
  'pink',
  'red',
  'orange',
  'amber',
  'gray',
]

/**
 * The icons offered for a habit (free names, D33 of the server), each drawn with an icon of the
 * set. The Android app offers the same names.
 */
export const HABIT_ICONS: Record<string, IconName> = {
  sparkles: 'sparkles',
  'book-open': 'book-open',
  book: 'book',
  droplet: 'droplet',
  dumbbell: 'dumbbell',
  bike: 'bike',
  'heart-pulse': 'heart-pulse',
  brain: 'brain',
  apple: 'apple',
  utensils: 'utensils',
  coffee: 'coffee',
  beer: 'beer',
  smartphone: 'smartphone',
  tv: 'tv',
  'gamepad-2': 'gamepad',
  music: 'music',
  palette: 'palette',
  camera: 'camera',
  pill: 'pill',
  toothbrush: 'toothbrush',
  'graduation-cap': 'graduation-cap',
  code: 'code',
  briefcase: 'briefcase',
  'piggy-bank': 'piggy-bank',
  'paw-print': 'paw-print',
  church: 'church',
  flame: 'flame',
  moon: 'moon',
  sun: 'sun',
  trophy: 'trophy',
}

/** The icon of a habit's name, or a generic one for a name this client doesn't know. */
export function habitIcon(name: string): IconName {
  return HABIT_ICONS[name] ?? 'list-checks'
}

export function iconOptions(t: Translate) {
  return Object.entries(HABIT_ICONS).map(([value, icon]) => ({
    value,
    icon,
    label: t(`habits.icons.${value}`),
  }))
}

export function colorTone(color: string): Tone {
  return `swatch-${color}`
}

export function swatchOptions(t: Translate, current?: string) {
  const values = [...PICKER_COLORS]
  if (current && ALL_COLORS.includes(current) && !values.includes(current)) values.push(current)
  return values.map((value) => ({
    value,
    label: t(`habits.colors.${value}`),
    color: `var(--color-swatch-${value})`,
  }))
}

type FrequencyShape = Pick<HabitFrequency, 'kind'> &
  Partial<
    Pick<
      HabitFrequency,
      | 'weekdays'
      | 'every_n_weeks'
      | 'month_days'
      | 'month_last_day'
      | 'week_of_month'
      | 'weekday'
      | 'every_n_months'
      | 'times'
      | 'period'
      | 'preferred_day'
      | 'times_per_week'
    >
  >

function listText(t: Translate, names: string[]): string {
  if (names.length < 2) return names[0] ?? ''
  return t('habits.frequency.list', { first: names.slice(0, -1).join(', '), last: names.at(-1) })
}

/** "sábado" (0 = Monday). */
export function weekdayName(t: Translate, weekday: number): string {
  return t('habits.frequency.weekdayLong').split(',')[weekday] ?? ''
}

function weekdaysText(t: Translate, weekdays: number[]): string {
  if (weekdays.length === 7) return t('habits.frequency.daily')
  if (weekdays.length === 5 && !weekdays.includes(5) && !weekdays.includes(6))
    return t('habits.frequency.workdays')
  if (weekdays.length === 1) return weekdayName(t, weekdays[0] ?? 0)
  const shorts = t('habits.frequency.weekdayNames').split(',')
  return listText(
    t,
    weekdays.map((day) => shorts[day] ?? ''),
  )
}

function everyText(t: Translate, unit: 'weeks' | 'months', n: number, rest: string): string {
  if (n <= 1) return rest
  const key =
    unit === 'weeks' && n === 2 ? 'habits.frequency.fortnightly' : `habits.frequency.every.${unit}`
  return `${t(key, { n })} · ${rest}`
}

/**
 * The frequency in words: "Todo dia", "Seg, Qua e Sex", "Quinzenal · sábado", "Dia 5",
 * "A cada 3 meses · dia 5", "1º domingo do mês", "2× por mês · de preferência dia 15".
 */
export function frequencyText(t: Translate, frequency: FrequencyShape): string {
  switch (frequency.kind) {
    case 'weekdays':
      return everyText(
        t,
        'weeks',
        frequency.every_n_weeks ?? 1,
        weekdaysText(t, frequency.weekdays ?? []),
      )
    case 'month_days': {
      const days = (frequency.month_days ?? []).map(String)
      if (frequency.month_last_day) days.push(t('habits.frequency.lastDay'))
      const text = frequency.month_days?.length
        ? t('habits.frequency.monthDays', { days: listText(t, days) }, days.length)
        : t('habits.frequency.lastDayOfMonth')
      return everyText(t, 'months', frequency.every_n_months ?? 1, text)
    }
    case 'month_weekday': {
      const weekday = frequency.weekday ?? 0
      const gender = weekday >= 5 ? 'm' : 'f'
      const week = frequency.week_of_month ?? 1
      const text = t('habits.frequency.monthWeekday', {
        nth: t(`habits.frequency.nth.${gender}.${week === -1 ? 'last' : week}`),
        weekday: weekdayName(t, weekday),
      })
      return everyText(t, 'months', frequency.every_n_months ?? 1, text)
    }
    case 'per_period':
    case 'weekly': {
      const period = frequency.period ?? 'week'
      const n = frequency.times ?? frequency.times_per_week ?? 1
      const text = t(`habits.frequency.perPeriod.${period}`, { n })
      const preferred = frequency.preferred_day
      if (preferred === null || preferred === undefined) return text
      const day =
        period === 'month'
          ? t('habits.frequency.dayOfMonth', { day: preferred })
          : weekdayName(t, preferred)
      return `${text} · ${t('habits.frequency.preferred', { day })}`
    }
    default:
      return t('habits.frequency.daily')
  }
}

/** "1 de 2 nesta quinzena · faltam 5 dias". */
export function periodText(t: Translate, period: HabitPeriod): string {
  const progress = t(`habits.period.${period.period}`, { done: period.done, target: period.target })
  if (period.done >= period.target) return progress
  return `${progress} · ${t('habits.period.daysLeft', period.days_left)}`
}

/** "12 dias", "3 semanas", "4 vezes", "2 meses". */
export function streakText(
  t: Translate,
  habit: Pick<Habit, 'current_streak' | 'streak_unit'>,
): string {
  const value = habit.current_streak ?? 0
  return t(`habits.streak.${habit.streak_unit ?? 'day'}`, value)
}

/** The window of the rate (H5), from the unit of the streak. */
export function rateHint(t: Translate, habit: Pick<Habit, 'streak_unit'>): string {
  return t(`habits.detail.rateWindow.${habit.streak_unit ?? 'day'}`)
}

/** "sáb, 28/11". */
export function dueText(t: Translate, on: string): string {
  const weekday = (new Date(`${on}T12:00:00`).getDay() + 6) % 7
  const short = t('habits.frequency.weekdayNames').split(',')[weekday] ?? ''
  return `${short.toLowerCase()}, ${dateShort(on)}`
}

/** A name without accents nor case, for searching ("agua" finds "Beber água"). */
export function searchable(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .trim()
}

/** "1.250 / 2.000 ml" for a quantity. */
export function amount(
  ref: Pick<HabitRef, 'target_value' | 'unit'>,
  value: number | null | undefined,
): string {
  return `${integer(value ?? 0)} / ${integer(ref.target_value ?? 0)} ${ref.unit ?? ''}`.trim()
}

/** `YYYY-MM` of a plain date. */
export function monthOf(day: string): string {
  return day.slice(0, 7)
}
