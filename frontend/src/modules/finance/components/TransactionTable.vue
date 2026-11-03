<script setup lang="ts">
/**
 * Transactions as a table. `compact` (Visão geral): date, description, category, account and
 * value. `full` (Transações): grouped by day, with icon, time and the row menu.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, weekdayDayMonth } from '@/lib/format'
import { PBadge, PIconButton, PMenu, PTable, PText, PTile, type MenuEntry } from '@/ui'

import type { Transaction } from '../api'
import { amountTone, signedAmount, today, transactionIcon, transactionTitle } from '../helpers'

const props = withDefaults(
  defineProps<{ transactions: Transaction[]; mode?: 'compact' | 'full'; caption: string }>(),
  { mode: 'compact' },
)
const emit = defineEmits<{ edit: [transaction: Transaction]; remove: [transaction: Transaction] }>()
const { t } = useI18n()

type Row = Record<string, unknown> & { id: string; transaction: Transaction }

const columns = computed(() => {
  const base = [
    { key: 'description', label: t('finance.table.description') },
    { key: 'category', label: t('finance.table.category') },
    { key: 'account', label: t('finance.table.account') },
    { key: 'value', label: t('finance.table.value'), align: 'end' as const },
  ]
  if (props.mode === 'compact') return [{ key: 'date', label: t('finance.table.date') }, ...base]
  return [
    ...base,
    { key: 'actions', label: t('finance.table.actions'), align: 'end' as const, hideLabel: true },
  ]
})

function row(transaction: Transaction): Row {
  return { id: transaction.id, transaction }
}

const rows = computed(() => props.transactions.map(row))
const groups = computed(() => {
  const byDay = new Map<string, Row[]>()
  for (const transaction of props.transactions) {
    const list = byDay.get(transaction.occurred_on) ?? []
    list.push(row(transaction))
    byDay.set(transaction.occurred_on, list)
  }
  const current = today()
  return [...byDay.entries()].map(([day, list]) => ({
    label:
      day === current
        ? `${weekdayDayMonth(day)} · ${t('finance.transactions.today')}`
        : weekdayDayMonth(day),
    rows: list,
  }))
})

function accountOf(transaction: Transaction): string {
  if (transaction.kind === 'transfer') return '—'
  if (transaction.credit_card && transaction.kind === 'expense')
    return t('finance.transactions.card', { name: transaction.credit_card.name })
  return transaction.account?.name ?? '—'
}

function categoryOf(transaction: Transaction): string {
  if (transaction.kind === 'transfer')
    return t('finance.events.transfer', {
      from: transaction.account?.name ?? '',
      to: transaction.destination_account?.name ?? '',
    })
  if (transaction.kind === 'card_payment')
    return t('finance.transactions.card', { name: transaction.credit_card?.name ?? '' })
  if (transaction.kind === 'adjustment') return t('finance.kinds.adjustment')
  return transaction.category?.name ?? ''
}

function badgeVariant(transaction: Transaction): 'soft' | 'outline' | 'dashed' {
  if (transaction.kind === 'transfer' || transaction.kind === 'card_payment') return 'outline'
  if (transaction.kind === 'adjustment') return 'dashed'
  return 'soft'
}

function subtitle(transaction: Transaction): string {
  const parts = [transaction.occurred_time?.slice(0, 5)]
  if (transaction.installment_number && transaction.installment_count)
    parts.push(
      t('finance.transactions.installment', {
        number: transaction.installment_number,
        count: transaction.installment_count,
      }),
    )
  return parts.filter(Boolean).join(' · ')
}

function menu(transaction: Transaction): MenuEntry[] {
  return [
    ...(transaction.kind === 'adjustment'
      ? []
      : [
          {
            label: t('finance.actions.edit'),
            icon: 'edit' as const,
            onSelect: () => emit('edit', transaction),
          },
        ]),
    {
      label: t('finance.actions.delete'),
      icon: 'trash',
      danger: true,
      onSelect: () => emit('remove', transaction),
    },
  ]
}

const cast = (value: Record<string, unknown>) => (value as Row).transaction
</script>

<template>
  <PTable
    :columns="columns"
    :rows="mode === 'compact' ? rows : undefined"
    :groups="mode === 'full' ? groups : undefined"
    :row-key="(value) => String(value.id)"
    :caption="caption"
  >
    <template #cell-date="{ row: value }">{{ dateShort(cast(value).occurred_on) }}</template>
    <template #cell-description="{ row: value }">
      <span v-if="mode === 'full'" class="table__description">
        <PTile :icon="transactionIcon(cast(value))" tone="finance" shape="circle" />
        <span class="table__titles">
          <PText variant="strong" as="span">{{ transactionTitle(cast(value), t) }}</PText>
          <PText v-if="subtitle(cast(value))" variant="sm" tone="muted" as="span">{{
            subtitle(cast(value))
          }}</PText>
        </span>
      </span>
      <PText v-else variant="strong" as="span">{{ transactionTitle(cast(value), t) }}</PText>
    </template>
    <template #cell-category="{ row: value }">
      <PBadge
        v-if="categoryOf(cast(value))"
        :tone="cast(value).kind === 'income' ? 'finance' : 'neutral'"
        :variant="badgeVariant(cast(value))"
        >{{ categoryOf(cast(value)) }}</PBadge
      >
    </template>
    <template #cell-account="{ row: value }">{{ accountOf(cast(value)) }}</template>
    <template #cell-value="{ row: value }">
      <PText
        variant="strong"
        as="span"
        :tone="amountTone(cast(value).kind, cast(value).amount_cents)"
        >{{ signedAmount(cast(value).kind, cast(value).amount_cents) }}</PText
      >
    </template>
    <template #cell-actions="{ row: value }">
      <PMenu :items="menu(cast(value))">
        <template #trigger><PIconButton icon="more" :label="t('finance.actions.more')" /></template>
      </PMenu>
    </template>
  </PTable>
</template>

<style scoped>
.table__description {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-3);
}

.table__titles {
  display: flex;
  min-width: 0;
  flex-direction: column;
}
</style>
