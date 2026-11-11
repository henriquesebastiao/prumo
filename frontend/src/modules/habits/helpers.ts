/** Presentation helpers of the habits module. */
import type { Translate } from '@/app/registry'
import { integer } from '@/lib/format'
import type { IconName, Tone } from '@/ui'

import type { Habit, HabitFrequency, HabitRef } from './api'

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

/** "Todo dia", "3× por semana", "Seg, Qua e Sex". */
export function frequencyText(
  t: Translate,
  frequency: Pick<HabitFrequency, 'kind' | 'times_per_week' | 'weekdays'>,
): string {
  if (frequency.kind === 'weekly')
    return t('habits.frequency.weekly', { n: frequency.times_per_week ?? 1 })
  if (frequency.kind === 'weekdays') {
    const shorts = t('habits.frequency.weekdayNames').split(',')
    const names = (frequency.weekdays ?? []).map((day) => shorts[day] ?? '')
    if (names.length === 5 && !frequency.weekdays?.includes(5) && !frequency.weekdays?.includes(6))
      return t('habits.frequency.workdays')
    return names.length > 1
      ? t('habits.frequency.list', { first: names.slice(0, -1).join(', '), last: names.at(-1) })
      : (names[0] ?? '')
  }
  return t('habits.frequency.daily')
}

/** "12 dias", "3 semanas". */
export function streakText(
  t: Translate,
  habit: Pick<Habit, 'current_streak' | 'streak_unit'>,
): string {
  const value = habit.current_streak ?? 0
  return habit.streak_unit === 'week'
    ? t('habits.streak.weeks', value)
    : t('habits.streak.days', value)
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
