import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import finance from '.'
import { describeActivity, describeUpcoming } from './events'
import { amountTone, dataIcon, monthRange, shiftMonth, signedAmount } from './helpers'

const t = i18n.global.t
/** Money uses no-break spaces; the expectations are written with plain ones. */
const plain = (text?: string) => text?.replace(/\u00a0/g, ' ')

describe('finance items on Início', async () => {
  await loadModuleMessages([finance])

  it('describes invoice closing and due dates', () => {
    const base = { module: 'finance', on: '2026-12-03', subject: 'Nubank', entity_id: 'c1' }
    const closing = describeUpcoming(
      {
        ...base,
        kind: 'finance.invoice_closing',
        data: { amount_cents: 128460, available_limit_cents: 371540 },
      },
      t,
    )
    expect(closing).toMatchObject({
      title: 'Fatura Nubank fecha',
      to: { name: 'finance.cards', query: { cartao: 'c1' } },
    })
    expect(plain(closing?.subtitle)).toBe('Limite disponível R$ 3.715,40')
    const due = { ...base, kind: 'finance.invoice_due' }
    expect(
      plain(
        describeUpcoming(
          {
            ...due,
            data: { amount_cents: 128460, paid_cents: 0, remaining_cents: 128460, status: 'open' },
          },
          t,
        )?.subtitle,
      ),
    ).toBe('R$ 1.284,60 até agora')
    expect(
      plain(
        describeUpcoming(
          {
            ...due,
            data: {
              amount_cents: 128460,
              paid_cents: 28460,
              remaining_cents: 100000,
              status: 'overdue',
            },
          },
          t,
        )?.subtitle,
      ),
    ).toBe('Vencida · faltam R$ 1.000,00')
    expect(describeUpcoming({ ...base, kind: 'garage.oil_change' }, t)).toBeNull()
  })

  it('describes transactions', () => {
    const view = describeActivity(
      {
        module: 'finance',
        kind: 'finance.transaction',
        occurred_at: new Date().toISOString(),
        subject: 'Supermercado',
        data: {
          transaction_kind: 'expense',
          amount_cents: 21240,
          category: 'Alimentação',
          account: 'Nubank',
          occurred_time: '11:25',
        },
      },
      t,
    )
    expect(view).toMatchObject({ title: 'Supermercado · Alimentação', icon: 'minus' })
    expect(plain(view?.value)).toBe('− R$ 212,40')
    expect(view?.subtitle).toMatch(/^Hoje, \d\d:\d\d · Nubank$/)
    const transfer = describeActivity(
      {
        module: 'finance',
        kind: 'finance.transaction',
        occurred_at: new Date().toISOString(),
        subject: '',
        data: {
          transaction_kind: 'transfer',
          amount_cents: 50000,
          account: 'Inter',
          destination_account: 'Nubank',
          occurred_time: null,
        },
      },
      t,
    )
    expect(transfer?.title).toBe('Transferência')
    expect(plain(transfer?.value)).toBe('R$ 500,00')
    expect(transfer?.subtitle).toBe('Hoje · Inter → Nubank')
  })
})

describe('finance helpers', () => {
  it('signs amounts by kind', () => {
    expect(plain(signedAmount('income', 150000))).toBe('+ R$ 1.500,00')
    expect(plain(signedAmount('expense', 1850))).toBe('− R$ 18,50')
    expect(plain(signedAmount('transfer', 50000))).toBe('R$ 500,00')
    expect(plain(signedAmount('adjustment', -300))).toBe('− R$ 3,00')
    expect(amountTone('income', 1)).toBe('success')
    expect(amountTone('expense', 1)).toBe('default')
  })

  it('maps API icons and months', () => {
    expect(dataIcon('house')).toBe('home')
    expect(dataIcon('unknown-icon', 'wallet')).toBe('wallet')
    expect(monthRange('2026-02')).toEqual({ from: '2026-02-01', to: '2026-02-28' })
    expect(shiftMonth('2026-01', -1)).toBe('2025-12')
    expect(shiftMonth('2026-12', 1)).toBe('2027-01')
  })
})
