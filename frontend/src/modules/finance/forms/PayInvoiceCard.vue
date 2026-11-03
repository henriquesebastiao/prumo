<script setup lang="ts">
/** "Pagar fatura": amount (total or partial), account and date of a card payment. */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PAlert,
  PButton,
  PCard,
  PDateInput,
  PField,
  PMoneyInput,
  PSelect,
  PText,
  useToast,
} from '@/ui'

import { useAccounts, usePayInvoice, type CreditCard, type Invoice } from '../api'
import { today } from '../helpers'
import { useFormErrors } from './useFinanceForm'

const props = defineProps<{ card: CreditCard; invoice: Invoice }>()
const { t } = useI18n()
const toast = useToast()
const pay = usePayInvoice()
const accounts = useAccounts()
const { errors, failure, capture, clear } = useFormErrors()

const amount = ref<number | null>(null)
const accountId = ref('')
const day = ref('')

function reset() {
  clear()
  amount.value = props.invoice.remaining_cents || null
  accountId.value =
    props.card.payment_account?.id ?? accounts.data.value?.items[0]?.id ?? accountId.value
  day.value = props.invoice.due_on >= today() ? props.invoice.due_on : today()
}
watch(() => [props.card.id, props.invoice.closing_on, props.invoice.remaining_cents], reset, {
  immediate: true,
})
watch(
  () => accounts.data.value,
  () => {
    if (!accountId.value) reset()
  },
)

const accountOptions = computed(() =>
  (accounts.data.value?.items ?? []).map((account) => ({ value: account.id, label: account.name })),
)

async function submit() {
  if (!amount.value || !accountId.value) return
  try {
    await pay.mutateAsync({
      cardId: props.card.id,
      closingOn: props.invoice.closing_on,
      body: { amount_cents: amount.value, account_id: accountId.value, occurred_on: day.value },
    })
    toast.show({ title: t('finance.cards.paid') })
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PCard as="form" :title="t('finance.cards.pay')" novalidate @submit.prevent="submit">
    <div class="form">
      <PAlert v-if="failure" :title="failure" />
      <PField
        :label="t('finance.cards.payAmount')"
        :hint="t('finance.cards.payAmountHint')"
        :error="errors.amount_cents"
      >
        <PMoneyInput v-model="amount" />
      </PField>
      <div class="form__row">
        <PField :label="t('finance.cards.payWith')" :error="errors.account_id">
          <PSelect v-model="accountId" :options="accountOptions" />
        </PField>
        <PField :label="t('finance.cards.payDate')" :error="errors.occurred_on">
          <PDateInput v-model="day" />
        </PField>
      </div>
      <PButton
        type="submit"
        variant="primary"
        size="lg"
        block
        :loading="pay.isPending.value"
        :disabled="!amount || !accountId"
        >{{ t('finance.actions.pay') }}</PButton
      >
      <PText variant="sm" tone="muted">{{ t('finance.cards.payHint') }}</PText>
    </div>
  </PCard>
</template>

<style src="./form.css" scoped></style>
