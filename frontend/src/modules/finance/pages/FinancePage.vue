<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute, useRouter } from 'vue-router'

import { PButton, PMonthNav, PPageHeader, PTabs } from '@/ui'

import TransactionDialog from '../forms/TransactionDialog.vue'
import { currentMonth } from '../helpers'
import { provideFinance } from './context'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/
const month = computed<string>({
  get: () => {
    const value = route.query.mes
    return typeof value === 'string' && MONTH.test(value) ? value : currentMonth()
  },
  set: (value) => {
    const query = { ...route.query, mes: value === currentMonth() ? undefined : value }
    void router.replace({ query })
  },
})

const createRequests = ref(0)
const transactionOpen = ref(false)
const transactionKind = ref<'expense' | 'income' | 'transfer'>('expense')
function newTransaction(kind: 'expense' | 'income' | 'transfer' = 'expense') {
  transactionKind.value = kind
  transactionOpen.value = true
}
provideFinance({ month, createRequests, newTransaction })

const current = computed(() => String(route.name ?? 'finance.home'))
const TITLES: Record<string, string> = {
  'finance.home': 'overview',
  'finance.transactions': 'transactions',
  'finance.accounts': 'accounts',
  'finance.cards': 'cards',
  'finance.categories': 'categories',
}
const section = computed(() => TITLES[current.value] ?? 'overview')
const createLabel = computed(
  () =>
    ({
      accounts: t('finance.actions.newAccount'),
      cards: t('finance.actions.newCard'),
      categories: t('finance.actions.newCategory'),
    })[section.value] ?? t('finance.actions.newTransaction'),
)
function create() {
  if (['accounts', 'cards', 'categories'].includes(section.value)) createRequests.value += 1
  else newTransaction()
}

const tabs = computed(() =>
  (['overview', 'transactions', 'accounts', 'cards', 'categories'] as const).map((key) => {
    const name = Object.keys(TITLES).find((route) => TITLES[route] === key) ?? 'finance.home'
    return { value: name, label: t(`finance.tabs.${key}`), to: { name } }
  }),
)
</script>

<template>
  <PPageHeader :overline="t('finance.nav')" :title="t(`finance.titles.${section}`)">
    <PMonthNav v-if="section === 'overview'" v-model="month" :label="t('finance.month')" />
    <PButton variant="primary" icon="add" @click="create">{{ createLabel }}</PButton>
  </PPageHeader>
  <PTabs mode="nav" :items="tabs" :model-value="current" :label="t('finance.tabs.label')" />
  <RouterView />
  <TransactionDialog v-model:open="transactionOpen" :kind="transactionKind" />
</template>
