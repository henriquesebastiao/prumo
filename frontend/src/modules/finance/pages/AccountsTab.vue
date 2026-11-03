<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { dateShort, money, monthName } from '@/lib/format'
import {
  PButton,
  PCard,
  PConfirmDialog,
  PEmptyState,
  PIconButton,
  PList,
  PListItem,
  PMenu,
  PNote,
  PQueryState,
  PText,
  PTile,
  useToast,
  type MenuEntry,
} from '@/ui'

import { useAccounts, useArchiveAccount, useDeleteAccount, type Account } from '../api'
import AccountForm from '../forms/AccountForm.vue'
import AdjustBalanceDialog from '../forms/AdjustBalanceDialog.vue'
import { colorTone, currentMonth, dataIcon, today } from '../helpers'
import { useFinance } from './context'

const { t, te } = useI18n()
const toast = useToast()
const { createRequests } = useFinance()
const query = useAccounts('all')
const archive = useArchiveAccount()
const remove = useDeleteAccount()

const active = computed(() => (query.data.value?.items ?? []).filter((a) => !a.archived_at))
const archived = computed(() => (query.data.value?.items ?? []).filter((a) => a.archived_at))
const monthLabel = computed(() => monthName(`${currentMonth()}-01`))

/** `undefined`: closed; `null`: new account; an account: editing it. */
const editing = ref<Account | null | undefined>(undefined)
const panel = ref<HTMLElement>()
async function openForm(account: Account | null) {
  editing.value = account
  await nextTick()
  panel.value?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
}
watch(createRequests, () => openForm(null))

const adjusting = ref<Account>()
const adjustOpen = ref(false)
const deleting = ref<Account>()
const deleteOpen = ref(false)

function updated(account: Account): string {
  if (!account.last_transaction_on) return t('finance.accounts.noMovement')
  return account.last_transaction_on === today()
    ? t('finance.accounts.updatedToday')
    : t('finance.accounts.updatedOn', { date: dateShort(account.last_transaction_on) })
}

function subtitle(account: Account): string {
  const parts = [
    t(`finance.accountKinds.${account.kind}`),
    t('finance.accounts.monthCount', { month: monthLabel.value }, account.month_transactions_count),
  ]
  if (!account.include_in_total) parts.push(t('finance.accounts.outOfTotal'))
  return parts.join(' · ')
}

async function setArchived(account: Account, value: boolean) {
  try {
    await archive.mutateAsync({ id: account.id, archived: value })
    if (value) toast.show({ title: t('finance.accounts.archivedToast') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

function menu(account: Account): MenuEntry[] {
  if (account.archived_at)
    return [
      {
        label: t('finance.actions.unarchive'),
        icon: 'refresh',
        onSelect: () => setArchived(account, false),
      },
    ]
  return [
    { label: t('finance.actions.edit'), icon: 'edit', onSelect: () => openForm(account) },
    {
      label: t('finance.actions.adjust'),
      icon: 'sliders',
      onSelect: () => {
        adjusting.value = account
        adjustOpen.value = true
      },
    },
    { type: 'separator' },
    account.transactions_count > 0
      ? {
          label: t('finance.actions.archive'),
          icon: 'archive',
          onSelect: () => setArchived(account, true),
        }
      : {
          label: t('finance.actions.delete'),
          icon: 'trash',
          danger: true,
          onSelect: () => {
            deleting.value = account
            deleteOpen.value = true
          },
        },
  ]
}

async function confirmDelete() {
  if (!deleting.value) return
  try {
    await remove.mutateAsync(deleting.value.id)
    toast.show({ title: t('finance.accounts.deleted') })
    deleteOpen.value = false
    if (editing.value?.id === deleting.value.id) editing.value = undefined
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <div class="accounts" :class="{ 'accounts--with-panel': editing !== undefined }">
    <div class="accounts__main">
      <PQueryState
        :loading="query.isPending.value"
        :error="query.error.value"
        :empty="active.length === 0 && archived.length === 0"
      >
        <PCard v-if="active.length" :title="t('finance.accounts.title')">
          <template #actions>
            <PText variant="sm" tone="secondary" as="span"
              >{{ t('finance.accounts.total') }}
              <PText variant="h2" as="b">{{
                money(query.data.value?.total_balance_cents ?? 0)
              }}</PText>
            </PText>
          </template>
          <PList>
            <PListItem
              v-for="account in active"
              :key="account.id"
              :title="account.name"
              :subtitle="subtitle(account)"
            >
              <template #leading>
                <PTile
                  :icon="dataIcon(account.icon, 'wallet')"
                  :tone="colorTone(account.color)"
                  size="lg"
                />
              </template>
              <template #trailing>
                <span class="accounts__value">
                  <PText variant="number-l" as="span">{{ money(account.balance_cents) }}</PText>
                  <PText variant="xs" tone="muted" as="span">{{ updated(account) }}</PText>
                </span>
                <PMenu :items="menu(account)">
                  <template #trigger>
                    <PIconButton icon="more" :label="t('finance.actions.more')" />
                  </template>
                </PMenu>
              </template>
            </PListItem>
          </PList>
          <PNote class="accounts__note">{{ t('finance.accounts.note') }}</PNote>
        </PCard>
        <PCard v-if="archived.length" :title="t('finance.accounts.archived')" variant="flat">
          <PList>
            <PListItem
              v-for="account in archived"
              :key="account.id"
              :title="account.name"
              :subtitle="t(`finance.accountKinds.${account.kind}`)"
            >
              <template #leading>
                <PTile :icon="dataIcon(account.icon, 'wallet')" />
              </template>
              <template #trailing>
                <PText variant="strong" as="span">{{ money(account.balance_cents) }}</PText>
                <PMenu :items="menu(account)">
                  <template #trigger>
                    <PIconButton icon="more" :label="t('finance.actions.more')" />
                  </template>
                </PMenu>
              </template>
            </PListItem>
          </PList>
        </PCard>
        <template #empty>
          <PEmptyState
            :title="t('finance.accounts.empty')"
            :description="t('finance.accounts.emptyHint')"
            icon="wallet"
            tone="finance"
            variant="card"
          >
            <PButton variant="primary" icon="add" @click="openForm(null)">{{
              t('finance.actions.newAccount')
            }}</PButton>
          </PEmptyState>
        </template>
      </PQueryState>
    </div>
    <div v-if="editing !== undefined" ref="panel" class="accounts__panel">
      <AccountForm
        :key="editing?.id ?? 'new'"
        :account="editing ?? undefined"
        @close="editing = undefined"
      />
    </div>
    <AdjustBalanceDialog v-model:open="adjustOpen" :account="adjusting" />
    <PConfirmDialog
      v-model:open="deleteOpen"
      :title="t('finance.accounts.deleteTitle')"
      :description="t('finance.accounts.deleteBody', { name: deleting?.name ?? '' })"
      :confirm-label="t('finance.actions.delete')"
      :loading="remove.isPending.value"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.accounts {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: minmax(0, 1fr);
}

.accounts--with-panel {
  grid-template-columns: minmax(0, 1.68fr) minmax(0, 1fr);
}

.accounts__main {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
}

.accounts__value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.accounts__note {
  margin-top: var(--space-4);
}

@media (width < 1000px) {
  .accounts--with-panel {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
