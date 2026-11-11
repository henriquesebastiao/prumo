import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import habits from '.'
import { amount, frequencyText, habitIcon, streakText } from './helpers'

const t = i18n.global.t

describe('habits helpers', async () => {
  await loadModuleMessages([habits])

  it('writes each frequency', () => {
    expect(frequencyText(t, { kind: 'daily', times_per_week: null, weekdays: null })).toBe(
      'Todo dia',
    )
    expect(frequencyText(t, { kind: 'weekly', times_per_week: 3, weekdays: null })).toBe(
      '3× por semana',
    )
    expect(
      frequencyText(t, { kind: 'weekdays', times_per_week: null, weekdays: [0, 1, 2, 3, 4] }),
    ).toBe('Dias úteis')
    expect(frequencyText(t, { kind: 'weekdays', times_per_week: null, weekdays: [0, 2, 4] })).toBe(
      'Seg, Qua e Sex',
    )
  })

  it('writes streaks in days or weeks', () => {
    expect(streakText(t, { current_streak: 1, streak_unit: 'day' })).toBe('1 dia')
    expect(streakText(t, { current_streak: 12, streak_unit: 'day' })).toBe('12 dias')
    expect(streakText(t, { current_streak: 3, streak_unit: 'week' })).toBe('3 semanas')
  })

  it('writes a quantity against its target', () => {
    expect(amount({ target_value: 2000, unit: 'ml' }, 1250)).toBe('1.250 / 2.000 ml')
  })

  it('falls back to a generic icon for an unknown name', () => {
    expect(habitIcon('dumbbell')).toBe('dumbbell')
    expect(habitIcon('rocket')).toBe('list-checks')
  })
})
