import { calendarDay } from '@/lib/format'

/** Today (`YYYY-MM-DD`) in the user's time zone: only a default of a field, never a rule. */
export function today(): string {
  return calendarDay(new Date())
}
