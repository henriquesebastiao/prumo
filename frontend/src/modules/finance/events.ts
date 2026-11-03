/** How the finance items of "Vem aí" and "Atividade recente" appear on Início. */
import type { EventView, Translate } from '@/app/registry'
import type { Schemas } from '@/lib/api/client'
import { money, relativeDateTime } from '@/lib/format'

import type { TransactionKind } from './api'
import { signedAmount } from './helpers'

type Data = Record<string, string | number | boolean | null | undefined>

const cents = (value: unknown): number => (typeof value === 'number' ? value : 0)

export function describeUpcoming(item: Schemas['UpcomingItem'], t: Translate): EventView | null {
  const data = (item.data ?? {}) as Data
  const card = { card: item.subject }
  const to = { name: 'finance.cards', query: item.entity_id ? { cartao: item.entity_id } : {} }
  if (item.kind === 'finance.invoice_closing') {
    return {
      title: t('finance.events.invoiceClosing', card),
      subtitle: t('finance.events.availableLimit', {
        value: money(cents(data.available_limit_cents)),
      }),
      to,
    }
  }
  if (item.kind === 'finance.invoice_due') {
    const remaining = money(cents(data.amount_cents) - cents(data.paid_cents))
    let subtitle = t('finance.events.dueAmount', { value: money(cents(data.amount_cents)) })
    if (data.status === 'overdue') subtitle = t('finance.events.overdue', { value: remaining })
    else if (cents(data.paid_cents) > 0)
      subtitle = t('finance.events.dueRemaining', { value: remaining })
    return { title: t('finance.events.invoiceDue', card), subtitle, to }
  }
  return null
}

const ICONS: Record<TransactionKind, EventView['icon']> = {
  income: 'add',
  expense: 'minus',
  transfer: 'transfer',
  card_payment: 'card',
  adjustment: 'sliders',
}

export function describeActivity(item: Schemas['ActivityItem'], t: Translate): EventView | null {
  if (item.kind !== 'finance.transaction') return null
  const data = (item.data ?? {}) as Data
  const kind = (data.transaction_kind ?? 'expense') as TransactionKind
  const description = item.subject || t(`finance.kinds.${kind}`)
  const title =
    typeof data.category === 'string'
      ? t('finance.events.transaction', { description, category: data.category })
      : description
  const when = data.occurred_time
    ? relativeDateTime(item.occurred_at)
    : relativeDateTime(item.occurred_at).split(',')[0]
  const where =
    kind === 'transfer' && typeof data.account === 'string'
      ? t('finance.events.transfer', { from: data.account, to: data.destination_account ?? '' })
      : typeof data.credit_card === 'string'
        ? t('finance.form.card', { name: data.credit_card })
        : data.account
  return {
    title,
    subtitle: [when, where].filter(Boolean).join(' · '),
    value: signedAmount(kind, cents(data.amount_cents)),
    icon: ICONS[kind],
    to: { name: 'finance.transactions' },
  }
}
