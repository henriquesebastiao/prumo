/** Presentation helpers of the studies module. */
import type { Translate } from '@/app/registry'
import type { Tone } from '@/ui'

import type { DayStatus } from './api'

export const COLORS = [
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
] as const
export type StudiesColor = (typeof COLORS)[number]
const PICKER_COLORS: StudiesColor[] = ['blue', 'violet', 'orange', 'green', 'pink', 'cyan', 'gray']

/** Tone of an area's color: `swatch-blue`. */
export function colorTone(color: string): Tone {
  return `swatch-${color}`
}

export function swatchOptions(t: Translate, current?: string) {
  const values = [...PICKER_COLORS]
  const known = COLORS.find((color) => color === current)
  if (known && !values.includes(known)) values.push(known)
  return values.map((value) => ({
    value,
    label: t(`studies.colors.${value}`),
    color: `var(--color-swatch-${value})`,
  }))
}

/** `1h 30` · `45 min` */
export function minutes(value: number): string {
  const hours = Math.floor(value / 60)
  const rest = value % 60
  if (!hours) return `${rest} min`
  return rest ? `${hours}h ${String(rest).padStart(2, '0')}` : `${hours}h`
}

/** `19:00` from the API's `19:00:00`. */
export function clock(value: string | null | undefined): string | undefined {
  return value ? value.slice(0, 5) : undefined
}

export const STATUS_TONE: Record<DayStatus, Tone> = {
  met: 'success',
  partial: 'warning',
  missed: 'danger',
  in_progress: 'neutral',
  extra: 'accent',
}

/** The chip durations of the session form. */
export const QUICK_MINUTES = [15, 25, 30, 45, 60]

/** Monday (`YYYY-MM-DD`) on or before a plain date. */
export function mondayOf(day: string): string {
  const [y, m, d] = day.split('-').map(Number) as [number, number, number]
  const date = new Date(Date.UTC(y, m - 1, d))
  const weekday = (date.getUTCDay() + 6) % 7
  date.setUTCDate(date.getUTCDate() - weekday)
  return date.toISOString().slice(0, 10)
}

/** The next Monday after a plain date (the default start of a plan version). */
export function nextMonday(day: string): string {
  const [y, m, d] = day.split('-').map(Number) as [number, number, number]
  const date = new Date(Date.UTC(y, m - 1, d))
  const weekday = (date.getUTCDay() + 6) % 7
  date.setUTCDate(date.getUTCDate() + (7 - weekday))
  return date.toISOString().slice(0, 10)
}

export function addDays(day: string, days: number): string {
  const [y, m, d] = day.split('-').map(Number) as [number, number, number]
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10)
}
