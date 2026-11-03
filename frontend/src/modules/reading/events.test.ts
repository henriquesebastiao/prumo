import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import reading from '.'
import { describeActivity } from './events'
import { coverVariant } from './helpers'

const t = i18n.global.t

describe('reading items on Início', async () => {
  await loadModuleMessages([reading])
  const base = {
    module: 'reading',
    occurred_at: new Date().toISOString(),
    subject: 'Código Limpo',
    entity_id: 'b1',
  }

  it('describes progress with the pages advanced', () => {
    const view = describeActivity(
      {
        ...base,
        kind: 'reading.progress',
        data: { page: 212, pages: 14, total_pages: 425, status: 'reading' },
      },
      t,
    )
    expect(view).toMatchObject({
      title: 'Leitura · Código Limpo',
      value: '+14 p.',
      icon: 'bookmark',
      to: { name: 'reading.book', params: { bookId: 'b1' } },
    })
    expect(view?.subtitle).toMatch(/^Hoje, \d\d:\d\d · até a página 212$/)
    const done = describeActivity(
      {
        ...base,
        kind: 'reading.progress',
        data: { page: 425, pages: 213, total_pages: 425, status: 'read' },
      },
      t,
    )
    expect(done?.title).toBe('Leitura concluída · Código Limpo')
  })

  it('describes notes and ignores other kinds', () => {
    const view = describeActivity(
      { ...base, kind: 'reading.note', data: { page: 98, excerpt: 'Funções pequenas.' } },
      t,
    )
    expect(view?.title).toBe('Anotação · Código Limpo')
    expect(view?.subtitle).toMatch(/· Funções pequenas\.$/)
    expect(describeActivity({ ...base, kind: 'garage.fueling' }, t)).toBeNull()
  })

  it('draws covers by status', () => {
    expect(coverVariant('reading')).toBe('tone')
    expect(coverVariant('want_to_read')).toBe('paper')
    expect(coverVariant('read')).toBe('ink')
  })
})
