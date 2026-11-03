<script setup lang="ts">
/** Creates or edits a credit card; archives or deletes it (F8). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PAlert,
  PButton,
  PDialog,
  PField,
  PInput,
  PMoneyInput,
  PNumberInput,
  PSelect,
  PSwatchPicker,
  useToast,
} from '@/ui'

import { useAccounts, useArchiveCard, useDeleteCard, useSaveCard, type CreditCard } from '../api'
import { swatchOptions, type FinanceColor } from '../helpers'
import { useFormErrors } from './useFinanceForm'

const props = defineProps<{ card?: CreditCard }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ removed: [] }>()
const { t } = useI18n()
const toast = useToast()
const save = useSaveCard()
const archive = useArchiveCard()
const remove = useDeleteCard()
const accounts = useAccounts()
const { errors, failure, capture, clear } = useFormErrors()

const name = ref('')
const limit = ref<number | null>(null)
const closingDay = ref<number | null>(null)
const dueDay = ref<number | null>(null)
const paymentAccount = ref('none')
const color = ref<FinanceColor>('violet')

watch(
  open,
  (value) => {
    if (!value) return
    clear()
    name.value = props.card?.name ?? ''
    limit.value = props.card?.limit_cents ?? null
    closingDay.value = props.card?.closing_day ?? null
    dueDay.value = props.card?.due_day ?? null
    paymentAccount.value = props.card?.payment_account?.id ?? 'none'
    color.value = (props.card?.color as FinanceColor | undefined) ?? 'violet'
  },
  { immediate: true },
)

const initialColor = computed(() => props.card?.color)
const accountOptions = computed(() => [
  { value: 'none', label: t('finance.cards.noPaymentAccount') },
  ...(accounts.data.value?.items ?? []).map((account) => ({
    value: account.id,
    label: account.name,
  })),
])

async function submit() {
  const body = {
    name: name.value,
    limit_cents: limit.value ?? 0,
    closing_day: closingDay.value ?? 0,
    due_day: dueDay.value ?? 0,
    payment_account_id: paymentAccount.value === 'none' ? null : paymentAccount.value,
    color: color.value,
  }
  try {
    await save.mutateAsync({ id: props.card?.id, body })
    toast.show({ title: t('finance.cards.saved') })
    open.value = false
  } catch (error) {
    capture(error)
  }
}

async function archiveOrDelete() {
  if (!props.card) return
  try {
    if (props.card.transactions_count > 0) {
      await archive.mutateAsync({ id: props.card.id, archived: true })
      toast.show({ title: t('finance.cards.archivedToast') })
    } else {
      await remove.mutateAsync(props.card.id)
      toast.show({ title: t('finance.cards.deleted') })
    }
    open.value = false
    emit('removed')
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="card ? t('finance.cards.editTitle') : t('finance.cards.newTitle')"
    icon="card"
    tone="finance"
  >
    <form id="card-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('finance.cards.name')" :error="errors.name">
          <PInput
            v-model="name"
            :placeholder="t('finance.cards.namePlaceholder')"
            :maxlength="60"
          />
        </PField>
        <PField :label="t('finance.cards.limitLabel')" :error="errors.limit_cents">
          <PMoneyInput v-model="limit" />
        </PField>
      </div>
      <div class="form__row">
        <PField
          :label="t('finance.cards.closingDay')"
          :hint="t('finance.cards.closingHint')"
          :error="errors.closing_day"
        >
          <PNumberInput v-model="closingDay" />
        </PField>
        <PField :label="t('finance.cards.dueDay')" :error="errors.due_day">
          <PNumberInput v-model="dueDay" />
        </PField>
      </div>
      <PField :label="t('finance.cards.paymentAccount')" :error="errors.payment_account_id">
        <PSelect v-model="paymentAccount" :options="accountOptions" />
      </PField>
      <PField :label="t('finance.cards.color')" label-as="span">
        <PSwatchPicker
          v-model="color"
          :options="swatchOptions(t, initialColor)"
          :label="t('finance.cards.color')"
        />
      </PField>
    </form>
    <template #footer>
      <PButton
        v-if="card"
        variant="ghost"
        class="form__footer-start"
        :loading="archive.isPending.value || remove.isPending.value"
        @click="archiveOrDelete"
        >{{
          card.transactions_count > 0 ? t('finance.actions.archive') : t('finance.actions.delete')
        }}</PButton
      >
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton type="submit" form="card-form" variant="primary" :loading="save.isPending.value">{{
        card ? t('ui.save') : t('finance.cards.create')
      }}</PButton>
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
