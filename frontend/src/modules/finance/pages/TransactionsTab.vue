<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { money, monthYear } from '@/lib/format'
import {
  PButton,
  PCard,
  PConfirmDialog,
  PDialog,
  PEmptyState,
  PQueryState,
  PSearchField,
  PSegmented,
  PSelect,
  PText,
  useToast,
} from '@/ui'

import {
  useAccounts,
  useCards,
  useCategories,
  useDeleteTransaction,
  useTransactions,
  type Transaction,
  type TransactionFilters,
  type TransactionKind,
} from '../api'
import TransactionTable from '../components/TransactionTable.vue'
import TransactionDialog from '../forms/TransactionDialog.vue'
import { currentMonth, monthRange, shiftMonth, transactionTitle } from '../helpers'
import { useFinance } from './context'

const PAGE = 10

const { t, te } = useI18n()
const toast = useToast()
const { month } = useFinance()

const search = ref('')
const query = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(timer)
  timer = setTimeout(() => (query.value = value.trim()), 300)
})
const kind = ref<'all' | TransactionKind>('all')
const source = ref('all')
const category = ref('all')

const accounts = useAccounts('all')
const cards = useCards('all')
const categories = useCategories()

const filters = computed<TransactionFilters>(() => {
  const value: TransactionFilters = { ...monthRange(month.value) }
  if (kind.value !== 'all') value.kind = kind.value
  const [type, id] = source.value.split(':')
  if (type === 'account' && id) value.account_id = id
  if (type === 'card' && id) value.credit_card_id = id
  if (category.value !== 'all') value.category_id = category.value
  if (query.value) value.q = query.value
  return value
})
const list = useTransactions(filters, PAGE)
const items = computed(() => list.data.value?.pages.flatMap((page) => page.items) ?? [])
const first = computed(() => list.data.value?.pages[0])

const monthOptions = computed(() => {
  const now = currentMonth()
  const months = Array.from({ length: 26 }, (_, index) => shiftMonth(now, 1 - index))
  if (!months.includes(month.value)) months.push(month.value)
  return months.map((value) => ({ value, label: monthYear(`${value}-01`) }))
})
const kindOptions = computed(() => [
  { value: 'all' as const, label: t('finance.transactions.all') },
  { value: 'expense' as const, label: t('finance.transactions.expenses') },
  { value: 'income' as const, label: t('finance.transactions.incomes') },
  { value: 'transfer' as const, label: t('finance.transactions.transfers') },
])
const sourceOptions = computed(() => [
  { value: 'all', label: t('finance.transactions.allAccounts') },
  ...(accounts.data.value?.items ?? []).map((account) => ({
    value: `account:${account.id}`,
    label: t('finance.transactions.accountFilter', { name: account.name }),
  })),
  ...(cards.data.value ?? []).map((card) => ({
    value: `card:${card.id}`,
    label: t('finance.transactions.accountFilter', {
      name: t('finance.transactions.card', { name: card.name }),
    }),
  })),
])
const categoryOptions = computed(() => [
  { value: 'all', label: t('finance.transactions.allCategories') },
  ...(categories.data.value?.items ?? []).map((item) => ({
    value: item.id,
    label: t('finance.transactions.categoryFilter', { name: item.name }),
  })),
])

const editing = ref<Transaction>()
const editOpen = ref(false)
function edit(transaction: Transaction) {
  editing.value = transaction
  editOpen.value = true
}

const removing = ref<Transaction>()
const removeOpen = ref(false)
const remove = useDeleteTransaction()
function askRemove(transaction: Transaction) {
  removing.value = transaction
  removeOpen.value = true
}
async function confirmRemove(all = false) {
  if (!removing.value) return
  try {
    await remove.mutateAsync({ id: removing.value.id, all })
    toast.show({ title: t('finance.transactions.deleted') })
    removeOpen.value = false
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <div class="transactions">
    <PCard as="div">
      <div class="transactions__filters">
        <div class="transactions__search">
          <PSearchField v-model="search" :placeholder="t('finance.transactions.search')" />
        </div>
        <div class="transactions__select">
          <PSelect v-model="month" :options="monthOptions" variant="filter" icon="calendar" />
        </div>
        <div class="transactions__select">
          <PSelect v-model="source" :options="sourceOptions" variant="filter" />
        </div>
        <div class="transactions__select">
          <PSelect v-model="category" :options="categoryOptions" variant="filter" />
        </div>
      </div>
      <div class="transactions__summary">
        <PSegmented
          v-model="kind"
          :options="kindOptions"
          :label="t('finance.transactions.kindFilter')"
        />
        <PText v-if="first" variant="sm" tone="secondary" as="span">
          {{ t('finance.transactions.count', first.total) }} ·
          <PText variant="sm" tone="success" weight="bold" as="span">{{
            money(first.income_cents, 'always')
          }}</PText>
          ·
          <PText variant="sm" weight="bold" as="span">{{ money(-first.expense_cents) }}</PText>
        </PText>
      </div>
    </PCard>

    <PCard as="div">
      <PQueryState
        :loading="list.isPending.value"
        :error="list.error.value"
        :empty="items.length === 0"
        :error-title="t('ui.loadFailed')"
      >
        <TransactionTable
          :transactions="items"
          mode="full"
          :caption="t('finance.titles.transactions')"
          @edit="edit"
          @remove="askRemove"
        />
        <div class="transactions__footer">
          <PText variant="sm" tone="muted">{{
            t('finance.transactions.showing', { shown: items.length, total: first?.total ?? 0 })
          }}</PText>
          <PButton
            v-if="list.hasNextPage.value"
            :loading="list.isFetchingNextPage.value"
            @click="list.fetchNextPage()"
            >{{ t('finance.actions.loadMore') }}</PButton
          >
        </div>
        <template #empty>
          <PEmptyState
            :title="t('finance.transactions.empty')"
            :description="t('finance.transactions.emptyHint')"
            icon="search"
          />
        </template>
      </PQueryState>
    </PCard>

    <TransactionDialog v-model:open="editOpen" :transaction="editing" />
    <PConfirmDialog
      v-if="removing && !removing.installment_group_id"
      v-model:open="removeOpen"
      :title="t('finance.transactions.deleteTitle')"
      :description="t('finance.transactions.deleteBody', { name: transactionTitle(removing, t) })"
      :confirm-label="t('finance.actions.delete')"
      :loading="remove.isPending.value"
      @confirm="confirmRemove()"
    />
    <PDialog
      v-else-if="removing"
      v-model:open="removeOpen"
      :title="t('finance.transactions.deleteTitle')"
      icon="trash"
      tone="danger"
      size="s"
    >
      <PText tone="secondary">{{
        t('finance.transactions.deleteInstallments', {
          number: removing.installment_number,
          count: removing.installment_count,
        })
      }}</PText>
      <template #footer>
        <PButton @click="removeOpen = false">{{ t('ui.cancel') }}</PButton>
        <PButton :loading="remove.isPending.value" @click="confirmRemove()">{{
          t('finance.transactions.deleteOne')
        }}</PButton>
        <PButton variant="danger" :loading="remove.isPending.value" @click="confirmRemove(true)">{{
          t('finance.actions.deleteAll')
        }}</PButton>
      </template>
    </PDialog>
  </div>
</template>

<style scoped>
.transactions {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.transactions__filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2-5);
}

.transactions__search {
  min-width: min(260px, 100%);
  flex: 1 1 320px;
}

.transactions__select {
  min-width: 0;
  flex: 0 1 220px;
}

.transactions__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.transactions__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-3);
}
</style>
