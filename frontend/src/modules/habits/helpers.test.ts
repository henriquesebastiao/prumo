import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import habits from '.'
import { draftOf, fieldsOf } from './forms/frequency'
import {
  amount,
  dueText,
  frequencyText,
  habitIcon,
  periodText,
  searchable,
  streakText,
} from './helpers'

const t = i18n.global.t

describe('habits helpers', async () => {
  await loadModuleMessages([habits])

  it.each([
    [{ kind: 'daily' as const }, 'Todo dia'],
    [{ kind: 'weekly' as const, times_per_week: 3 }, '3× por semana'],
    [{ kind: 'weekdays' as const, weekdays: [0, 1, 2, 3, 4], every_n_weeks: 1 }, 'Dias úteis'],
    [{ kind: 'weekdays' as const, weekdays: [0, 2, 4], every_n_weeks: 1 }, 'Seg, Qua e Sex'],
    [{ kind: 'weekdays' as const, weekdays: [5], every_n_weeks: 2 }, 'Quinzenal · sábado'],
    [{ kind: 'weekdays' as const, weekdays: [5], every_n_weeks: 3 }, 'A cada 3 semanas · sábado'],
    [{ kind: 'month_days' as const, month_days: [5], every_n_months: 1 }, 'Dia 5'],
    [{ kind: 'month_days' as const, month_days: [5], every_n_months: 3 }, 'A cada 3 meses · Dia 5'],
    [
      { kind: 'month_days' as const, month_days: [1, 15], month_last_day: true },
      'Dias 1, 15 e último dia',
    ],
    [{ kind: 'month_days' as const, month_days: [], month_last_day: true }, 'Último dia do mês'],
    [{ kind: 'month_weekday' as const, week_of_month: 1, weekday: 6 }, '1º domingo do mês'],
    [{ kind: 'month_weekday' as const, week_of_month: -1, weekday: 4 }, 'Última sexta do mês'],
    [{ kind: 'per_period' as const, times: 2, period: 'fortnight' as const }, '2× por quinzena'],
    [
      { kind: 'per_period' as const, times: 1, period: 'month' as const, preferred_day: 15 },
      '1× por mês · de preferência dia 15',
    ],
    [
      { kind: 'per_period' as const, times: 3, period: 'week' as const, preferred_day: 5 },
      '3× por semana · de preferência sábado',
    ],
  ])('writes the frequency %o', (frequency, text) => {
    expect(frequencyText(t, frequency)).toBe(text)
  })

  it('writes streaks in each unit', () => {
    expect(streakText(t, { current_streak: 1, streak_unit: 'day' })).toBe('1 dia')
    expect(streakText(t, { current_streak: 12, streak_unit: 'day' })).toBe('12 dias')
    expect(streakText(t, { current_streak: 3, streak_unit: 'week' })).toBe('3 semanas')
    expect(streakText(t, { current_streak: 4, streak_unit: 'occurrence' })).toBe('4 vezes')
    expect(streakText(t, { current_streak: 2, streak_unit: 'month' })).toBe('2 meses')
  })

  it('writes the period in progress', () => {
    const period = {
      period: 'fortnight' as const,
      starts_on: '2026-11-09',
      ends_on: '2026-11-22',
      done: 1,
      target: 2,
      days_left: 5,
      neutral: false,
    }
    expect(periodText(t, period)).toBe('1 de 2 nesta quinzena · faltam 5 dias')
    expect(periodText(t, { ...period, done: 2 })).toBe('2 de 2 nesta quinzena')
  })

  it('writes the next day and searches without accents', () => {
    expect(dueText(t, '2026-11-28')).toBe('sáb, 28/11')
    expect(searchable(' Beber Água ')).toBe('beber agua')
  })

  it('turns a draft into the fields of each kind', () => {
    const draft = draftOf()
    expect(fieldsOf(draft)).toEqual({ kind: 'daily' })
    expect(fieldsOf({ ...draft, kind: 'per_period', times: 20, period: 'fortnight' })).toEqual({
      kind: 'per_period',
      times: 14,
      period: 'fortnight',
      preferred_day: null,
    })
    expect(
      draftOf({ kind: 'weekly', times_per_week: 4 } as Parameters<typeof draftOf>[0]).kind,
    ).toBe('per_period')
  })

  it('writes a quantity against its target', () => {
    expect(amount({ target_value: 2000, unit: 'ml' }, 1250)).toBe('1.250 / 2.000 ml')
  })

  it('falls back to a generic icon for an unknown name', () => {
    expect(habitIcon('dumbbell')).toBe('dumbbell')
    expect(habitIcon('rocket')).toBe('list-checks')
  })
})
