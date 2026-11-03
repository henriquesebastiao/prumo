<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, decimal, formatConfig, money, moneyAmount, percent } from '@/lib/format'
import { PCard, PChart, PEmptyState, PLink, PQueryState, PStatCard, PStatus, PText } from '@/ui'

import { useOverview, useTransactions } from '../api'
import AccountBalances from '../components/AccountBalances.vue'
import InvoicePanel from '../components/InvoicePanel.vue'
import TransactionTable from '../components/TransactionTable.vue'
import { monthRange, today } from '../helpers'
import { useFinance } from './context'

const { t } = useI18n()
const { month } = useFinance()
const overview = useOverview(month)
/** The latest transactions up to today (scheduled ones are not "últimas"). */
const latest = useTransactions(() => {
  const range = monthRange(month.value)
  return { from: range.from, to: range.to < today() ? range.to : today() }
}, 4)
const data = computed(() => overview.data.value)

const latestItems = computed(() => latest.data.value?.pages[0]?.items ?? [])

/** "Salário e freelance": names of the income categories of the month. */
const incomeCaption = computed(() => {
  const names = (data.value?.income_by_category ?? []).map((share, index) =>
    index === 0 ? share.category.name : share.category.name.toLocaleLowerCase(),
  )
  return names.length
    ? new Intl.ListFormat(formatConfig().locale, { type: 'conjunction' }).format(names)
    : undefined
})

const expenseCaption = computed(() =>
  data.value?.expense_percent === null || data.value?.expense_percent === undefined
    ? t('finance.overview.noIncome')
    : t('finance.overview.ofIncome', { percent: percent(data.value.expense_percent) }),
)

const series = computed(() =>
  (data.value?.series ?? []).map((point) => ({
    label: new Intl.DateTimeFormat(formatConfig().locale, { month: 'short', timeZone: 'UTC' })
      .format(new Date(`${point.month}-01T00:00:00Z`))
      .replace('.', ''),
    values: [point.income_cents, point.expense_cents],
    highlight: point.month === month.value,
  })),
)
const thousands = (cents: number) =>
  t('finance.overview.thousands', { value: decimal(cents / 100_000, 1) })

/** The donut shows four slices; the rest goes to "Outras". */
const slices = computed(() => {
  const shares = data.value?.expenses_by_category ?? []
  const top = shares.slice(0, 4).map((share) => ({
    label: share.category.name,
    value: share.amount_cents,
  }))
  const rest = shares.slice(4).reduce((sum, share) => sum + share.amount_cents, 0)
  return rest > 0 ? [...top, { label: t('finance.overview.others'), value: rest }] : top
})
</script>

<template>
  <PQueryState
    :loading="overview.isPending.value"
    :error="overview.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div v-if="data" class="overview">
      <div class="overview__stats">
        <PStatCard
          :label="t('finance.overview.totalBalance')"
          :value="money(data.total_balance_cents)"
          :caption="t('finance.overview.accounts', data.accounts_count)"
        />
        <PStatCard
          :label="t('finance.overview.income')"
          :value="money(data.income_cents)"
          :caption="incomeCaption"
        />
        <PStatCard
          :label="t('finance.overview.expenses')"
          :value="money(data.expense_cents)"
          :caption="expenseCaption"
        />
        <PStatCard
          :label="t('finance.overview.result')"
          :value="money(data.result_cents, 'always')"
          :caption="t('finance.overview.until', { date: dateShort(data.until) })"
          :value-tone="data.result_cents < 0 ? 'danger' : 'success'"
        />
      </div>

      <div class="overview__row">
        <PCard :title="t('finance.overview.chart')">
          <template #actions>
            <span class="overview__legend">
              <PStatus tone="finance">{{ t('finance.overview.income') }}</PStatus>
              <PStatus>{{ t('finance.overview.expenses') }}</PStatus>
            </span>
          </template>
          <PChart
            type="grouped"
            tone="finance"
            :label="t('finance.overview.chartLabel')"
            :series="[t('finance.overview.income'), t('finance.overview.expenses')]"
            :data="series"
            value-labels="highlight"
            :height="210"
            :format="thousands"
          />
        </PCard>
        <PCard :title="t('finance.overview.byCategory')">
          <template #actions>
            <PLink :to="{ name: 'finance.categories', query: $route.query }" :chevron="false">{{
              t('finance.tabs.categories')
            }}</PLink>
          </template>
          <PChart
            v-if="slices.length"
            type="donut"
            tone="finance"
            legend
            :height="140"
            :label="t('finance.overview.byCategory')"
            :data="slices"
            :format="moneyAmount"
          >
            <template #center>
              <PText variant="xs" tone="muted" as="span">{{ t('finance.overview.total') }}</PText>
              <PText variant="h3" as="span">{{ moneyAmount(data.expense_cents) }}</PText>
            </template>
          </PChart>
          <PText v-else variant="sm" tone="muted">{{
            t('finance.overview.byCategoryEmpty')
          }}</PText>
        </PCard>
      </div>

      <div class="overview__row">
        <PCard :title="t('finance.overview.balances')">
          <template #actions>
            <PLink :to="{ name: 'finance.accounts' }" :chevron="false">{{
              t('finance.tabs.accounts')
            }}</PLink>
          </template>
          <AccountBalances v-if="data.accounts.length" :balances="data.accounts" />
          <PEmptyState v-else :title="t('finance.overview.noAccounts')" icon="wallet" />
        </PCard>
        <PCard :title="t('finance.overview.openInvoices')">
          <template #actions>
            <PLink :to="{ name: 'finance.cards' }" :chevron="false">{{
              t('finance.tabs.cards')
            }}</PLink>
          </template>
          <div v-if="data.open_invoices.length" class="overview__invoices">
            <InvoicePanel
              v-for="item in data.open_invoices"
              :key="`${item.card.id}-${item.invoice.closing_on}`"
              :item="item"
            />
          </div>
          <PText v-else variant="sm" tone="muted">{{ t('finance.overview.noInvoices') }}</PText>
        </PCard>
      </div>

      <PCard :title="t('finance.overview.latest')">
        <template #actions>
          <PLink :to="{ name: 'finance.transactions', query: $route.query }">{{
            t('finance.actions.seeAll')
          }}</PLink>
        </template>
        <TransactionTable
          v-if="latestItems.length"
          :transactions="latestItems"
          :caption="t('finance.overview.latest')"
        />
        <PText v-else variant="sm" tone="muted">{{ t('finance.overview.latestEmpty') }}</PText>
      </PCard>
    </div>
  </PQueryState>
</template>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.overview__stats {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
}

.overview__row {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: minmax(0, 1.68fr) minmax(0, 1fr);
}

.overview__legend {
  display: flex;
  gap: var(--space-4);
}

.overview__invoices {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

@media (width < 1000px) {
  .overview__row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
