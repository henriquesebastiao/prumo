import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import studies from '.'
import { describeActivity } from './events'
import { minutes, mondayOf, nextMonday } from './helpers'

const t = i18n.global.t

describe('studies items on Início', async () => {
  await loadModuleMessages([studies])
  const base = {
    module: 'studies',
    occurred_at: new Date().toISOString(),
    subject: 'FastAPI',
    entity_id: 's1',
  }

  it('describes a session with its topic and minutes', () => {
    const view = describeActivity(
      {
        ...base,
        kind: 'studies.session',
        data: { session_id: 'x', topic: 'Testes', duration_minutes: 45, color: 'green' },
      },
      t,
    )
    expect(view).toMatchObject({
      title: 'Estudo · FastAPI',
      value: '45 min',
      to: { name: 'studies.subject', params: { subjectId: 's1' } },
    })
    expect(view?.subtitle).toContain('Testes')
  })

  it('ignores kinds it does not know', () => {
    expect(describeActivity({ ...base, kind: 'studies.exam', data: {} }, t)).toBeNull()
  })
})

describe('studies helpers', () => {
  it('formats minutes as hours', () => {
    expect(minutes(45)).toBe('45 min')
    expect(minutes(60)).toBe('1h')
    expect(minutes(90)).toBe('1h 30')
    expect(minutes(125)).toBe('2h 05')
  })

  it('finds the Monday of a week and the next one', () => {
    expect(mondayOf('2026-11-17')).toBe('2026-11-16')
    expect(mondayOf('2026-11-16')).toBe('2026-11-16')
    expect(mondayOf('2026-11-22')).toBe('2026-11-16')
    expect(nextMonday('2026-11-17')).toBe('2026-11-23')
    expect(nextMonday('2026-11-16')).toBe('2026-11-23')
  })
})
