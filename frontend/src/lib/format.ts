/**
 * Display formatting with Intl, using the user's locale, time zone and currency (preferences).
 * Inputs follow the API: money in cents, volume in millilitres, distance in km, UTC date-times
 * and plain dates (`YYYY-MM-DD`) for calendar days. No business rule lives here.
 */

export interface FormatConfig {
  locale: string
  timeZone: string
  currency: string
}

const DEFAULTS: FormatConfig = {
  locale: 'pt-BR',
  timeZone: 'America/Sao_Paulo',
  currency: 'BRL',
}

let config: FormatConfig = { ...DEFAULTS }
const cache = new Map<string, Intl.NumberFormat | Intl.DateTimeFormat | Intl.RelativeTimeFormat>()

export function configureFormat(next: Partial<FormatConfig>): void {
  config = { ...config, ...next }
  cache.clear()
}

export function resetFormat(): void {
  configureFormat(DEFAULTS)
}

export function formatConfig(): Readonly<FormatConfig> {
  return config
}

function memo<T extends Intl.NumberFormat | Intl.DateTimeFormat | Intl.RelativeTimeFormat>(
  key: string,
  build: () => T,
): T {
  const full = `${config.locale}|${config.timeZone}|${config.currency}|${key}`
  let formatter = cache.get(full) as T | undefined
  if (!formatter) {
    formatter = build()
    cache.set(full, formatter)
  }
  return formatter
}

const MINUS = '−'

function capitalize(text: string): string {
  return text.charAt(0).toLocaleUpperCase(config.locale) + text.slice(1)
}

// ------------------------------------------------------------------ numbers

export function integer(value: number): string {
  return memo(
    'int',
    () => new Intl.NumberFormat(config.locale, { maximumFractionDigits: 0 }),
  ).format(value)
}

export function decimal(value: number, digits = 1): string {
  return memo(
    `dec${digits}`,
    () =>
      new Intl.NumberFormat(config.locale, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }),
  ).format(value)
}

export function percent(value: number, digits = 0): string {
  return memo(
    `pct${digits}`,
    () =>
      new Intl.NumberFormat(config.locale, {
        style: 'percent',
        maximumFractionDigits: digits,
      }),
  ).format(value / 100)
}

export function km(value: number): string {
  return `${integer(value)} km`
}

/** Litres from millilitres: `7300` → `7,30 L`. */
export function liters(ml: number, digits = 2): string {
  return `${decimal(ml / 1000, digits)} L`
}

// ------------------------------------------------------------------ money

export type SignDisplay = 'negative' | 'always' | 'never'

function currencyFormatter() {
  return memo(
    'money',
    () => new Intl.NumberFormat(config.locale, { style: 'currency', currency: config.currency }),
  )
}

export interface MoneyParts {
  sign: '' | '+' | typeof MINUS
  symbol: string
  amount: string
}

export function moneyParts(cents: number, sign: SignDisplay = 'negative'): MoneyParts {
  const parts = currencyFormatter().formatToParts(Math.abs(cents) / 100)
  const symbol = parts.find((part) => part.type === 'currency')?.value ?? config.currency
  const amount = parts
    .filter((part) => ['integer', 'group', 'decimal', 'fraction'].includes(part.type))
    .map((part) => part.value)
    .join('')
  let prefix: MoneyParts['sign'] = ''
  if (sign !== 'never') {
    if (cents < 0) prefix = MINUS
    else if (sign === 'always' && cents > 0) prefix = '+'
  }
  return { sign: prefix, symbol, amount }
}

/** `1234567` → `R$ 12.345,67`; with `sign: 'always'`, `+ R$ …` / `− R$ …`. */
export function money(cents: number, sign: SignDisplay = 'negative'): string {
  const { sign: prefix, symbol, amount } = moneyParts(cents, sign)
  const value = `${symbol} ${amount}`
  return prefix ? `${prefix} ${value}` : value
}

/** Amount without currency symbol: `R$ 4.812,37` → `4.812,37`. */
export function moneyAmount(cents: number): string {
  return moneyParts(cents, 'never').amount
}

// ------------------------------------------------------------------ dates

type DateInput = string | Date

const PLAIN_DATE = /^(\d{4})-(\d{2})-(\d{2})$/

/** A plain date (`2026-11-17`) is a calendar day: it is formatted in UTC so it never shifts. */
function toDate(value: DateInput): { date: Date; plain: boolean } {
  if (value instanceof Date) return { date: value, plain: false }
  const match = PLAIN_DATE.exec(value)
  if (match) {
    const [, year, month, day] = match
    return { date: new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))), plain: true }
  }
  return { date: new Date(value), plain: false }
}

function dateFormatter(key: string, options: Intl.DateTimeFormatOptions, plain: boolean) {
  const timeZone = plain ? 'UTC' : config.timeZone
  return memo(
    `${key}|${plain}`,
    () => new Intl.DateTimeFormat(config.locale, { ...options, timeZone }),
  )
}

function parts(value: DateInput, key: string, options: Intl.DateTimeFormatOptions) {
  const { date, plain } = toDate(value)
  const list = dateFormatter(key, options, plain).formatToParts(date)
  return (type: Intl.DateTimeFormatPartTypes) =>
    list.find((part) => part.type === type)?.value ?? ''
}

/** `17/11/2026` */
export function date(value: DateInput): string {
  const { date: d, plain } = toDate(value)
  return dateFormatter('date', { day: '2-digit', month: '2-digit', year: 'numeric' }, plain).format(
    d,
  )
}

/** `17/11` */
export function dateShort(value: DateInput): string {
  const { date: d, plain } = toDate(value)
  return dateFormatter('dateShort', { day: '2-digit', month: '2-digit' }, plain).format(d)
}

/** `14:30` */
export function time(value: DateInput): string {
  const { date: d, plain } = toDate(value)
  return dateFormatter(
    'time',
    { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' },
    plain,
  ).format(d)
}

/** `17/11/2026 · 14:30` */
export function dateTime(value: DateInput): string {
  return `${date(value)} · ${time(value)}`
}

/** `Novembro de 2026` */
export function monthYear(value: DateInput): string {
  const { date: d, plain } = toDate(value)
  return capitalize(dateFormatter('monthYear', { month: 'long', year: 'numeric' }, plain).format(d))
}

/** `Terça, 17 de novembro de 2026` (or without the year). */
export function weekdayDate(value: DateInput, withYear = true): string {
  const get = parts(value, 'weekday', { weekday: 'long', day: 'numeric', month: 'long' })
  const weekday = capitalize(get('weekday').replace(/-feira$/, ''))
  const year = withYear ? ` de ${parts(value, 'year', { year: 'numeric' })('year')}` : ''
  return `${weekday}, ${get('day')} de ${get('month')}${year}`
}

/** Day and abbreviated month for date badges: `{ day: '25', month: 'nov' }`. */
export function dayMonth(value: DateInput): { day: string; month: string } {
  const get = parts(value, 'dayMonth', { day: '2-digit', month: 'short' })
  return { day: get('day'), month: get('month').replace('.', '') }
}

/** Calendar day (`YYYY-MM-DD`) of a moment in the configured time zone. */
export function calendarDay(value: DateInput): string {
  const get = parts(value, 'iso', { year: 'numeric', month: '2-digit', day: '2-digit' })
  return `${get('year')}-${get('month')}-${get('day')}`
}

/** `Hoje, 07:42` · `Ontem, 18:10` · `15/11, 22:05` */
export function relativeDateTime(value: DateInput, now: Date = new Date()): string {
  const day = calendarDay(value)
  const today = calendarDay(now)
  const yesterday = calendarDay(new Date(now.getTime() - 86_400_000))
  const relative = memo(
    'rel',
    () => new Intl.RelativeTimeFormat(config.locale, { numeric: 'auto' }),
  )
  let label = dateShort(value)
  if (day === today) label = capitalize(relative.format(0, 'day'))
  else if (day === yesterday) label = capitalize(relative.format(-1, 'day'))
  return `${label}, ${time(value)}`
}

/** Hour (0–23) of a moment in the configured time zone. */
export function hourOf(value: DateInput = new Date()): number {
  return Number(parts(value, 'hour', { hour: '2-digit', hourCycle: 'h23' })('hour'))
}

export type DayPeriod = 'morning' | 'afternoon' | 'evening'

/** Part of the day used by greetings: before 12h, before 18h, after. */
export function dayPeriod(value: DateInput = new Date()): DayPeriod {
  const hour = hourOf(value)
  if (hour >= 5 && hour < 12) return 'morning'
  if (hour >= 12 && hour < 18) return 'afternoon'
  return 'evening'
}
