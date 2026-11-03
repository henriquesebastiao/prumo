<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, money, moneyAmount, moneyParts, monthYear, percent } from '@/lib/format'
import { PCard, PChart, PEmptyState, PIcon, PPanel, PProgress, PText } from '@/ui'

import type { FinanceSummary } from '../api'

const props = defineProps<{ summary?: FinanceSummary }>()
const { t } = useI18n()

const total = computed(() => moneyParts(props.summary?.total_balance_cents ?? 0))
const accounts = computed(() => (props.summary?.accounts ?? []).slice(0, 3))
const expenseShare = computed(() => {
  const summary = props.summary
  if (!summary || summary.income_cents <= 0) return summary?.expense_cents ? 100 : 0
  return Math.min(100, (summary.expense_cents / summary.income_cents) * 100)
})
const categories = computed(() =>
  (props.summary?.expenses_by_category ?? []).slice(0, 4).map((share) => ({
    label: share.category.name,
    value: share.amount_cents,
  })),
)
const invoice = computed(() => props.summary?.next_invoice ?? null)
</script>

<template>
  <PCard
    as="article"
    :title="t('finance.nav')"
    :subtitle="summary ? monthYear(`${summary.month}-01`) : undefined"
    icon="wallet"
    tone="finance"
    :link-label="t('finance.actions.open')"
    :to="{ name: 'finance.home' }"
  >
    <template v-if="summary && summary.accounts.length">
      <div class="widget__stack-xs">
        <PText variant="sm" tone="muted">{{ t('finance.widget.totalBalance') }}</PText>
        <PText variant="number-xl"
          ><small>{{ total.sign }}{{ total.symbol }}</small> {{ total.amount }}</PText
        >
      </div>
      <div class="widget__accounts">
        <PPanel v-for="item in accounts" :key="item.account.id" padding="sm">
          <PText variant="xs" tone="muted">{{ item.account.name }}</PText>
          <PText variant="h3">{{ moneyAmount(item.balance_cents) }}</PText>
        </PPanel>
      </div>
      <div class="widget__stack-s">
        <div class="widget__between">
          <PText variant="sm" tone="secondary">{{ t('finance.widget.income') }}</PText>
          <PText variant="sm" weight="bold">{{ money(summary.income_cents) }}</PText>
        </div>
        <PProgress
          :value="summary.income_cents > 0 ? 100 : 0"
          tone="finance"
          :label="t('finance.widget.income')"
        />
        <div class="widget__between">
          <PText variant="sm" tone="secondary">{{
            summary.expense_percent === null
              ? t('finance.widget.expenses')
              : t('finance.widget.expensesPercent', { percent: percent(summary.expense_percent) })
          }}</PText>
          <PText variant="sm" weight="bold">{{ money(summary.expense_cents) }}</PText>
        </div>
        <PProgress
          :value="expenseShare"
          tone="finance"
          strong
          :label="t('finance.widget.expenses')"
        />
      </div>
      <div v-if="categories.length" class="widget__stack-s">
        <PText variant="sm" tone="muted">{{ t('finance.widget.byCategory') }}</PText>
        <PChart
          type="stacked"
          tone="finance"
          :label="t('finance.widget.byCategory')"
          legend
          :data="categories"
          :format="moneyAmount"
        />
      </div>
      <PPanel v-if="invoice" padding="sm" class="widget__invoice">
        <PIcon name="card" data-tone="finance" />
        <PText variant="sm" class="widget__grow">{{
          t('finance.widget.invoice', { card: invoice.card.name })
        }}</PText>
        <PText variant="sm" weight="bold">{{ money(invoice.invoice.remaining_cents) }}</PText>
        <PText variant="sm" tone="muted">{{
          t('finance.widget.due', { date: dateShort(invoice.invoice.due_on) })
        }}</PText>
      </PPanel>
    </template>
    <PEmptyState v-else :title="t('finance.widget.empty')" icon="wallet" tone="finance" />
  </PCard>
</template>

<style scoped>
.widget__stack-xs {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-0-5);
}

.widget__stack-s {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-2);
}

.widget__between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.widget__accounts {
  display: grid;
  gap: var(--space-2);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.widget__invoice {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.widget__grow {
  min-width: 0;
  flex: 1;
}
</style>
