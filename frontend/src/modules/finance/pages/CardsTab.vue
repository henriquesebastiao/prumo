<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { date, dateShort, money, monthName } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PCardFace,
  PDescriptionList,
  PEmptyState,
  PList,
  PListItem,
  PProgress,
  PQueryState,
  PSegmented,
  PTable,
  PText,
  type StatusTone,
} from '@/ui'

import { useCards, useInvoice, useInvoices, type Invoice } from '../api'
import CardDialog from '../forms/CardDialog.vue'
import PayInvoiceCard from '../forms/PayInvoiceCard.vue'
import { colorTone } from '../helpers'
import { useFinance } from './context'

const ROWS = 7

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { createRequests } = useFinance()
const cards = useCards()
const list = computed(() => cards.data.value ?? [])

const cardId = computed<string>({
  get: () => {
    const wanted = route.query.cartao
    return list.value.find((card) => card.id === wanted)?.id ?? list.value[0]?.id ?? ''
  },
  set: (value) =>
    void router.replace({ query: { ...route.query, cartao: value, fatura: undefined } }),
})
const card = computed(() => list.value.find((item) => item.id === cardId.value))
const cardOptions = computed(() => list.value.map((item) => ({ value: item.id, label: item.name })))

const invoices = useInvoices(cardId)
/** The invoice in view: the `fatura` query parameter, or the current one. */
const selectedClosing = computed(() =>
  typeof route.query.fatura === 'string' ? route.query.fatura : '',
)
const invoiceLink = (closing?: string) => ({ query: { ...route.query, fatura: closing } })
const currentClosing = computed(() => card.value?.current_invoice.closing_on ?? '')
const closingOn = computed(() => selectedClosing.value || currentClosing.value)
const invoice = useInvoice(cardId, closingOn)
const selected = computed<Invoice | undefined>(
  () =>
    invoices.data.value?.find((item) => item.closing_on === closingOn.value) ??
    card.value?.current_invoice,
)
const previous = computed(() =>
  (invoices.data.value ?? []).filter((item) => item.closing_on < currentClosing.value),
)
const upcoming = computed(() =>
  (invoices.data.value ?? []).filter((item) => item.closing_on > currentClosing.value).reverse(),
)

const expanded = ref(false)
watch(closingOn, () => (expanded.value = false))
const entries = computed(() => invoice.data.value?.transactions ?? [])
const shownEntries = computed(() => (expanded.value ? entries.value : entries.value.slice(0, ROWS)))

const STATUS_TONES: Record<Invoice['status'], StatusTone> = {
  open: 'success',
  closed: 'warning',
  paid: 'neutral',
  overdue: 'danger',
}
const capitalized = (text: string) => text.charAt(0).toLocaleUpperCase() + text.slice(1)
const invoiceMonth = (item: Invoice) => monthName(item.due_on)

const details = computed(() =>
  card.value
    ? [
        { label: t('finance.cards.name'), value: card.value.name },
        { label: t('finance.cards.limitLabel'), value: money(card.value.limit_cents) },
        {
          label: t('finance.cards.closing'),
          value: t('finance.cards.day', { day: card.value.closing_day }),
        },
        {
          label: t('finance.cards.due'),
          value: t('finance.cards.day', { day: card.value.due_day }),
        },
        {
          label: t('finance.cards.paymentAccount'),
          value: card.value.payment_account?.name ?? t('finance.cards.noPaymentAccount'),
        },
      ]
    : [],
)

function invoiceCaption(item: Invoice): string {
  if (item.status === 'paid' && item.last_payment_on)
    return item.last_payment_account
      ? t('finance.cards.paidOn', {
          date: dateShort(item.last_payment_on),
          account: item.last_payment_account.name,
        })
      : t('finance.cards.paidOnPlain', { date: dateShort(item.last_payment_on) })
  return t('finance.cards.dueOn', { date: dateShort(item.due_on) })
}

const columns = computed(() => [
  { key: 'date', label: t('finance.table.date') },
  { key: 'description', label: t('finance.table.description') },
  { key: 'category', label: t('finance.table.category') },
  { key: 'value', label: t('finance.table.value'), align: 'end' as const },
])
const rows = computed(() =>
  shownEntries.value.map((entry) => ({
    id: entry.id,
    date: dateShort(entry.occurred_on),
    description: entry.installment_count
      ? `${entry.description} · ${t('finance.transactions.installment', {
          number: entry.installment_number,
          count: entry.installment_count,
        })}`
      : entry.description,
    category: entry.category?.name ?? '',
    value: money(entry.amount_cents),
  })),
)

const dialogOpen = ref(false)
const dialogCard = ref<typeof card.value>()
function openDialog(editing: boolean) {
  dialogCard.value = editing ? card.value : undefined
  dialogOpen.value = true
}
watch(createRequests, () => openDialog(false))
</script>

<template>
  <PQueryState
    :loading="cards.isPending.value"
    :error="cards.error.value"
    :empty="list.length === 0"
  >
    <div v-if="card" class="cards">
      <div class="cards__main">
        <PSegmented
          v-if="list.length > 1"
          v-model="cardId"
          :options="cardOptions"
          :label="t('finance.cards.choose')"
        />
        <PCard as="div">
          <div class="cards__summary">
            <div class="cards__face">
              <PCardFace
                :name="card.name"
                :caption="t('finance.cards.days', { closing: card.closing_day, due: card.due_day })"
                :tone="colorTone(card.color)"
              />
            </div>
            <div class="cards__usage">
              <PText variant="h2" as="h2">{{ card.name }}</PText>
              <div class="cards__between">
                <PText variant="sm" tone="secondary" as="span">{{ t('finance.cards.used') }}</PText>
                <PText variant="sm" weight="bold" as="span">{{ money(card.used_cents) }}</PText>
              </div>
              <PProgress
                :value="card.used_cents"
                :max="Math.max(1, card.limit_cents)"
                tone="finance"
                size="lg"
                :label="t('finance.cards.used')"
              />
              <div class="cards__between">
                <PText variant="sm" tone="secondary" as="span"
                  >{{ t('finance.cards.available') }}
                  <PText variant="sm" weight="bold" tone="default" as="b">{{
                    money(card.available_limit_cents)
                  }}</PText></PText
                >
                <PText variant="sm" tone="muted" as="span">{{
                  t('finance.cards.limit', { value: money(card.limit_cents) })
                }}</PText>
              </div>
            </div>
          </div>
        </PCard>

        <PCard v-if="selected" as="div">
          <template #header>
            <div class="cards__invoice-head">
              <div>
                <PText variant="h2" as="h2">{{
                  t('finance.cards.invoiceOf', { month: invoiceMonth(selected) })
                }}</PText>
                <PText variant="sm" tone="muted">{{
                  t('finance.cards.period', {
                    start: dateShort(selected.starts_on),
                    end: dateShort(selected.ends_on),
                    due: date(selected.due_on),
                  })
                }}</PText>
              </div>
              <div class="cards__invoice-total">
                <PBadge :tone="STATUS_TONES[selected.status]">{{
                  t(`finance.cards.status.${selected.status}`)
                }}</PBadge>
                <PText variant="number-l" as="span">{{ money(selected.amount_cents) }}</PText>
              </div>
            </div>
          </template>
          <PQueryState :loading="invoice.isPending.value" :error="invoice.error.value">
            <PTable
              v-if="rows.length"
              :columns="columns"
              :rows="rows"
              :row-key="(row) => String(row.id)"
              :caption="t('finance.cards.invoiceOf', { month: invoiceMonth(selected) })"
            >
              <template #cell-description="{ row }">
                <PText variant="strong" as="span">{{ row.description }}</PText>
              </template>
              <template #cell-category="{ row }">
                <PBadge v-if="row.category">{{ row.category }}</PBadge>
              </template>
              <template #cell-value="{ row }">
                <PText variant="strong" as="span">{{ row.value }}</PText>
              </template>
            </PTable>
            <PText v-else variant="sm" tone="muted">{{ t('finance.cards.noEntries') }}</PText>
            <div v-if="entries.length" class="cards__between cards__footer">
              <PText variant="sm" tone="muted" as="span">{{
                t('finance.cards.entries', { shown: shownEntries.length, total: entries.length })
              }}</PText>
              <PButton
                v-if="entries.length > ROWS && !expanded"
                variant="ghost"
                icon-right="chevron-right"
                @click="expanded = true"
                >{{ t('finance.cards.seeAll') }}</PButton
              >
            </div>
          </PQueryState>
        </PCard>
      </div>

      <div class="cards__side">
        <PayInvoiceCard
          v-if="selected && selected.remaining_cents > 0"
          :card="card"
          :invoice="selected"
        />
        <PCard v-else-if="selected" :title="t('finance.cards.pay')">
          <PText variant="sm" tone="muted">{{ t('finance.cards.nothingToPay') }}</PText>
        </PCard>

        <PCard :title="t('finance.cards.details')">
          <template #actions>
            <PButton variant="ghost" @click="openDialog(true)">{{
              t('finance.actions.edit')
            }}</PButton>
          </template>
          <PDescriptionList :items="details" />
        </PCard>

        <PCard v-if="upcoming.length" :title="t('finance.cards.upcoming')">
          <PList>
            <PListItem
              v-for="item in upcoming"
              :key="item.closing_on"
              :title="capitalized(invoiceMonth(item))"
              :subtitle="invoiceCaption(item)"
              :current="item.closing_on === closingOn"
              :to="invoiceLink(item.closing_on)"
            >
              <template #trailing>
                <PText variant="strong" as="span">{{ money(item.amount_cents) }}</PText>
              </template>
            </PListItem>
          </PList>
        </PCard>

        <PCard :title="t('finance.cards.previous')">
          <PList v-if="previous.length">
            <PListItem
              v-for="item in previous"
              :key="item.closing_on"
              :title="capitalized(invoiceMonth(item))"
              :subtitle="invoiceCaption(item)"
              :current="item.closing_on === closingOn"
              :to="invoiceLink(item.closing_on)"
            >
              <template #trailing>
                <PBadge :tone="STATUS_TONES[item.status]">{{
                  t(`finance.cards.status.${item.status}`)
                }}</PBadge>
                <PText variant="strong" as="span">{{ money(item.amount_cents) }}</PText>
              </template>
            </PListItem>
          </PList>
          <PText v-else variant="sm" tone="muted">{{ t('finance.cards.noPrevious') }}</PText>
          <PButton
            v-if="selectedClosing && selectedClosing !== currentClosing"
            variant="ghost"
            :to="invoiceLink(undefined)"
            >{{
              t('finance.cards.invoiceOf', { month: monthName(card.current_invoice.due_on) })
            }}</PButton
          >
        </PCard>
      </div>
    </div>
    <template #empty>
      <PEmptyState
        :title="t('finance.cards.empty')"
        :description="t('finance.cards.emptyHint')"
        icon="card"
        tone="finance"
        variant="card"
      >
        <PButton variant="primary" icon="add" @click="openDialog(false)">{{
          t('finance.actions.newCard')
        }}</PButton>
      </PEmptyState>
    </template>
  </PQueryState>
  <CardDialog v-model:open="dialogOpen" :card="dialogCard" />
</template>

<style scoped>
.cards {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: minmax(0, 1.68fr) minmax(0, 1fr);
}

.cards__main,
.cards__side {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
}

.cards__summary {
  display: grid;
  align-items: center;
  gap: var(--space-6);
  grid-template-columns: minmax(0, 280px) minmax(0, 1fr);
}

.cards__usage {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-3);
}

.cards__between {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.cards__invoice-head {
  display: flex;
  width: 100%;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.cards__invoice-total {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.cards__footer {
  margin-top: var(--space-4);
}

@media (width < 1000px) {
  .cards {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (width < 700px) {
  .cards__summary {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
