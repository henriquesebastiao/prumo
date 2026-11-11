import { calendarDay } from '@/lib/format'

/** Today (`YYYY-MM-DD`) in the user's time zone, to prefill date fields. */
export function today(): string {
  return calendarDay(new Date())
}
