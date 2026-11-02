import { afterEach, describe, expect, it } from 'vitest'

import {
  configureFormat,
  date,
  dateShort,
  dateTime,
  dayMonth,
  dayPeriod,
  decimal,
  integer,
  km,
  liters,
  money,
  moneyAmount,
  moneyParts,
  monthYear,
  percent,
  relativeDateTime,
  resetFormat,
  time,
  weekdayDate,
} from './format'

const NBSP = ' '

afterEach(() => resetFormat())

describe('numbers', () => {
  it('formats pt-BR numbers and units', () => {
    expect(integer(18420)).toBe('18.420')
    expect(decimal(40.36)).toBe('40,4')
    expect(percent(48)).toBe('48%')
    expect(km(52300)).toBe('52.300 km')
    expect(liters(7300)).toBe('7,30 L')
    expect(liters(26300)).toBe('26,30 L')
  })
})

describe('money', () => {
  it('formats cents', () => {
    expect(money(715427)).toBe(`R$${NBSP}7.154,27`)
    expect(money(0)).toBe(`R$${NBSP}0,00`)
    expect(moneyAmount(481237)).toBe('4.812,37')
  })

  it('handles signs with a real minus sign', () => {
    expect(money(-21240)).toBe(`− R$${NBSP}212,40`)
    expect(money(150000, 'always')).toBe(`+ R$${NBSP}1.500,00`)
    expect(money(-21240, 'never')).toBe(`R$${NBSP}212,40`)
  })

  it('splits symbol and amount', () => {
    expect(moneyParts(715427)).toEqual({ sign: '', symbol: 'R$', amount: '7.154,27' })
  })

  it('follows the configured currency', () => {
    configureFormat({ currency: 'USD' })
    expect(money(1999)).toBe(`US$${NBSP}19,99`)
  })
})

describe('dates', () => {
  const moment = '2026-11-17T17:30:00Z' // 14:30 in São Paulo

  it('formats moments in the user time zone', () => {
    expect(date(moment)).toBe('17/11/2026')
    expect(dateShort(moment)).toBe('17/11')
    expect(time(moment)).toBe('14:30')
    expect(dateTime(moment)).toBe('17/11/2026 · 14:30')
    configureFormat({ timeZone: 'Asia/Tokyo' })
    expect(date(moment)).toBe('18/11/2026')
  })

  it('never shifts plain dates', () => {
    configureFormat({ timeZone: 'Pacific/Honolulu' })
    expect(date('2026-11-02')).toBe('02/11/2026')
    configureFormat({ timeZone: 'Pacific/Kiritimati' })
    expect(date('2026-11-02')).toBe('02/11/2026')
  })

  it('formats long forms like the design', () => {
    expect(weekdayDate(moment)).toBe('Terça, 17 de novembro de 2026')
    expect(weekdayDate(moment, false)).toBe('Terça, 17 de novembro')
    expect(monthYear('2026-11-01')).toBe('Novembro de 2026')
    expect(dayMonth('2026-11-25')).toEqual({ day: '25', month: 'nov' })
  })

  it('uses today and yesterday', () => {
    const now = new Date('2026-11-17T17:30:00Z')
    expect(relativeDateTime('2026-11-17T10:42:00Z', now)).toBe('Hoje, 07:42')
    expect(relativeDateTime('2026-11-16T21:10:00Z', now)).toBe('Ontem, 18:10')
    expect(relativeDateTime('2026-11-16T01:05:00Z', now)).toBe('15/11, 22:05')
  })

  it('finds the part of the day in the user time zone', () => {
    expect(dayPeriod('2026-11-17T12:00:00Z')).toBe('morning') // 09:00
    expect(dayPeriod('2026-11-17T17:30:00Z')).toBe('afternoon') // 14:30
    expect(dayPeriod('2026-11-17T23:00:00Z')).toBe('evening') // 20:00
  })
})

describe('form date-times', () => {
  it('converts local day and time to UTC and back', async () => {
    const { zonedToIso, isoToZoned, daysUntil } = await import('./format')
    expect(zonedToIso('2026-11-17', '14:30')).toBe('2026-11-17T17:30:00Z')
    expect(zonedToIso('2026-11-17', '14:30', 'Asia/Tokyo')).toBe('2026-11-17T05:30:00Z')
    expect(zonedToIso('2026-07-01', '12:00', 'Europe/Lisbon')).toBe('2026-07-01T11:00:00Z')
    expect(isoToZoned('2026-11-17T02:30:00Z')).toEqual({ day: '2026-11-16', time: '23:30' })
    expect(daysUntil('2026-11-25', new Date('2026-11-17T17:30:00Z'))).toBe(8)
    expect(daysUntil('2026-11-16', new Date('2026-11-17T17:30:00Z'))).toBe(-1)
  })
})
