<script setup lang="ts">
/** F11: informs the real balance; the API records an adjustment with the difference. */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { money } from '@/lib/format'
import { PAlert, PButton, PDateInput, PDialog, PField, PMoneyInput, PText, useToast } from '@/ui'

import { useAdjustBalance, type Account } from '../api'
import { today } from '../helpers'
import { useFormErrors } from './useFinanceForm'

const props = defineProps<{ account?: Account }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const toast = useToast()
const adjust = useAdjustBalance()
const { errors, failure, capture, clear } = useFormErrors()

const balance = ref<number | null>(null)
const day = ref('')
watch(open, (value) => {
  if (!value) return
  clear()
  balance.value = props.account?.balance_cents ?? null
  day.value = today()
})

async function submit() {
  if (!props.account || balance.value === null) return
  try {
    await adjust.mutateAsync({
      id: props.account.id,
      body: { balance_cents: balance.value, occurred_on: day.value },
    })
    toast.show({ title: t('finance.accounts.adjusted') })
    open.value = false
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('finance.accounts.adjustTitle')"
    :description="account?.name"
    icon="sliders"
    tone="finance"
    size="s"
  >
    <form id="adjust-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PText v-if="account" variant="sm" tone="secondary">{{
        t('finance.accounts.adjustCurrent', { balance: money(account.balance_cents) })
      }}</PText>
      <div class="form__row">
        <PField :label="t('finance.accounts.adjustBalance')" :error="errors.balance_cents">
          <PMoneyInput v-model="balance" />
        </PField>
        <PField :label="t('finance.accounts.adjustDate')" :error="errors.occurred_on">
          <PDateInput v-model="day" />
        </PField>
      </div>
      <PText variant="sm" tone="muted">{{ t('finance.accounts.adjustHint') }}</PText>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="adjust-form"
        variant="primary"
        :loading="adjust.isPending.value"
        >{{ t('finance.accounts.adjustSave') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
