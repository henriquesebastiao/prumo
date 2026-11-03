<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { money } from '@/lib/format'
import {
  PAlert,
  PButton,
  PCheckbox,
  PChipChoice,
  PDateInput,
  PDialog,
  PField,
  PIconButton,
  PInput,
  PMoneyInput,
  PSegmented,
  PSelect,
  PText,
  useToast,
  type IconName,
} from '@/ui'

import {
  useAccounts,
  useCards,
  useCategories,
  useSaveCategory,
  useSaveTransaction,
  type Transaction,
} from '../api'
import { dataIcon, today } from '../helpers'
import { useFormErrors } from './useFinanceForm'

type FormKind = 'expense' | 'income' | 'transfer'

const props = defineProps<{ kind?: FormKind; transaction?: Transaction }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const toast = useToast()
const save = useSaveTransaction()
const saveCategory = useSaveCategory()
const { errors, failure, capture, clear } = useFormErrors()

const accountsQuery = useAccounts()
const cardsQuery = useCards()
const categoriesQuery = useCategories()
const accounts = computed(() => accountsQuery.data.value?.items ?? [])
const cards = computed(() => cardsQuery.data.value ?? [])

const formKind = ref<FormKind>('expense')
const amount = ref<number | null>(null)
const description = ref('')
const day = ref('')
const time = ref('')
/** Expense and income: `account:<id>` or `card:<id>`. */
const source = ref('')
const fromId = ref('')
const toId = ref('')
const categoryId = ref('')
const installments = ref('1')
const another = ref(false)
const newCategory = ref<string | null>(null)

const editing = computed(() => Boolean(props.transaction))
/** Card payments and adjustments only edit the common fields. */
const simple = computed(
  () => props.transaction?.kind === 'card_payment' || props.transaction?.kind === 'adjustment',
)
const isCard = computed(() => source.value.startsWith('card:'))

function firstAccount(except?: string): string {
  return accounts.value.find((account) => account.id !== except)?.id ?? ''
}

function reset() {
  clear()
  newCategory.value = null
  installments.value = '1'
  const transaction = props.transaction
  if (transaction) {
    formKind.value =
      transaction.kind === 'income' || transaction.kind === 'transfer'
        ? transaction.kind
        : 'expense'
    amount.value = Math.abs(transaction.amount_cents)
    description.value = transaction.description
    day.value = transaction.occurred_on
    time.value = transaction.occurred_time?.slice(0, 5) ?? ''
    source.value = transaction.credit_card
      ? `card:${transaction.credit_card.id}`
      : `account:${transaction.account?.id ?? ''}`
    fromId.value = transaction.account?.id ?? ''
    toId.value = transaction.destination_account?.id ?? ''
    categoryId.value = transaction.category?.id ?? ''
    return
  }
  formKind.value = props.kind ?? 'expense'
  amount.value = null
  description.value = ''
  day.value = today()
  time.value = ''
  source.value = accounts.value.length ? `account:${firstAccount()}` : ''
  fromId.value = firstAccount()
  toId.value = firstAccount(fromId.value)
  categoryId.value = ''
}
watch(open, (value) => value && reset(), { immediate: true })
watch(accounts, () => {
  if (props.transaction) return
  if (!source.value && accounts.value.length) source.value = `account:${firstAccount()}`
  if (!fromId.value) fromId.value = firstAccount()
  if (!toId.value) toId.value = firstAccount(fromId.value)
})
watch(formKind, (value) => {
  clear()
  if (value === 'income' && isCard.value) source.value = `account:${firstAccount()}`
  const category = categoryOptions.value.find((option) => option.value === categoryId.value)
  if (!category) categoryId.value = ''
})

const kindOptions = computed(() => [
  { value: 'expense' as const, label: t('finance.kinds.expense'), icon: 'minus' as const },
  { value: 'income' as const, label: t('finance.kinds.income'), icon: 'add' as const },
  { value: 'transfer' as const, label: t('finance.kinds.transfer'), icon: 'transfer' as const },
])

const sourceOptions = computed(() => [
  ...accounts.value.map((account) => ({ value: `account:${account.id}`, label: account.name })),
  ...(formKind.value === 'expense'
    ? cards.value.map((card) => ({
        value: `card:${card.id}`,
        label: t('finance.form.card', { name: card.name }),
        icon: 'card' as IconName,
      }))
    : []),
])

const accountOptions = computed(() =>
  accounts.value.map((account) => ({
    value: account.id,
    label: t('finance.form.accountBalance', {
      name: account.name,
      balance: money(account.balance_cents),
    }),
  })),
)

const categoryOptions = computed(() => {
  const items = (categoriesQuery.data.value?.items ?? []).filter(
    (category) => category.kind === formKind.value,
  )
  const options = items.map((category) => ({
    value: category.id,
    label: category.name,
    icon: dataIcon(category.icon),
  }))
  const current = props.transaction?.category
  if (current && current.kind === formKind.value && !options.some((o) => o.value === current.id))
    options.push({ value: current.id, label: current.name, icon: dataIcon(current.icon) })
  return options
})

const installmentOptions = computed(() =>
  Array.from({ length: 24 }, (_, index) => ({
    value: String(index + 1),
    label: index === 0 ? t('finance.form.single') : t('finance.form.times', { n: index + 1 }),
  })),
)

function swap() {
  ;[fromId.value, toId.value] = [toId.value, fromId.value]
}

async function addCategory() {
  const name = newCategory.value?.trim()
  if (!name || formKind.value === 'transfer') return
  try {
    const created = await saveCategory.mutateAsync({ body: { kind: formKind.value, name } })
    categoryId.value = created.id
    newCategory.value = null
  } catch (error) {
    capture(error)
  }
}

function body() {
  const common = {
    amount_cents: amount.value ?? 0,
    occurred_on: day.value,
    occurred_time: time.value || null,
    description: description.value,
  }
  if (simple.value) return common
  if (formKind.value === 'transfer')
    return { ...common, account_id: fromId.value, destination_account_id: toId.value }
  const [type, id] = source.value.split(':') as [string, string]
  const references = {
    category_id: categoryId.value || null,
    account_id: type === 'account' ? id || null : null,
    credit_card_id: type === 'card' ? id : null,
  }
  return { ...common, ...references }
}

async function submit() {
  if (amount.value === null || amount.value <= 0) {
    clear()
    errors.value = { amount_cents: t('errors.finance.invalid_amount') }
    return
  }
  const count = Number(installments.value)
  try {
    await save.mutateAsync(
      props.transaction
        ? { id: props.transaction.id, body: body() }
        : {
            body: {
              kind: formKind.value,
              ...body(),
              installments: isCard.value && count > 1 ? count : null,
            },
          },
    )
    toast.show({ title: t('finance.form.saved') })
    if (another.value && !editing.value) {
      amount.value = null
      description.value = ''
      installments.value = '1'
    } else {
      open.value = false
    }
  } catch (error) {
    capture(error)
  }
}

const submitLabel = computed(() => {
  if (simple.value || editing.value) return t('finance.form.save')
  return {
    expense: t('finance.form.saveExpense'),
    income: t('finance.form.saveIncome'),
    transfer: t('finance.form.saveTransfer'),
  }[formKind.value]
})
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="editing ? t('finance.form.editTitle') : t('finance.form.newTitle')"
    tone="finance"
  >
    <form id="transaction-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="accountsQuery.isSuccess.value && !accounts.length" tone="secondary">{{
        t('finance.form.noAccounts')
      }}</PText>
      <PSegmented
        v-if="!editing"
        v-model="formKind"
        :options="kindOptions"
        :label="t('finance.form.kind')"
        block
      />
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('finance.form.amount')" :error="errors.amount_cents" data-autofocus>
        <PMoneyInput v-model="amount" size="lg" />
      </PField>

      <template v-if="formKind !== 'transfer' || simple">
        <div class="form__row form__row--wide">
          <PField
            :label="t('finance.form.description')"
            :error="errors.description"
            :optional="simple"
          >
            <PInput
              v-model="description"
              :placeholder="t('finance.form.descriptionPlaceholder')"
              :maxlength="120"
            />
          </PField>
          <PField :label="t('finance.form.date')" :error="errors.occurred_on">
            <PDateInput v-model="day" />
          </PField>
          <PField :label="t('finance.form.time')" optional>
            <PDateInput v-model="time" type="time" />
          </PField>
        </div>
        <template v-if="!simple">
          <PField
            :label="t('finance.form.source')"
            label-as="span"
            :error="errors.account_id ?? errors.credit_card_id"
          >
            <PSegmented
              v-if="sourceOptions.length <= 5"
              v-model="source"
              :options="sourceOptions"
              :label="t('finance.form.source')"
            />
            <PSelect v-else v-model="source" :options="sourceOptions" />
          </PField>
          <PField
            v-if="isCard && !editing"
            :label="t('finance.form.installments')"
            :hint="t('finance.form.installmentsHint')"
          >
            <PSelect v-model="installments" :options="installmentOptions" />
          </PField>
          <PField :label="t('finance.form.category')" label-as="span" :error="errors.category_id">
            <div class="form__stack">
              <PChipChoice
                v-model="categoryId"
                :options="categoryOptions"
                :label="t('finance.form.category')"
                tone="finance"
              />
              <PText v-if="categoriesQuery.isSuccess.value && !categoryOptions.length" variant="sm">
                {{ t('finance.form.noCategories') }}
              </PText>
              <div v-if="newCategory !== null" class="form__inline">
                <PField :error="errors.name">
                  <PInput
                    v-model="newCategory"
                    :placeholder="t('finance.categories.name')"
                    :maxlength="40"
                    @keydown.enter.prevent="addCategory"
                  />
                </PField>
                <PButton :loading="saveCategory.isPending.value" @click="addCategory">{{
                  t('ui.save')
                }}</PButton>
              </div>
              <div v-else>
                <PButton variant="ghost" icon="add" @click="newCategory = ''">{{
                  t('finance.form.newCategory')
                }}</PButton>
              </div>
            </div>
          </PField>
        </template>
      </template>

      <template v-else>
        <PField :label="t('finance.form.from')" :error="errors.account_id">
          <PSelect v-model="fromId" :options="accountOptions" />
        </PField>
        <div class="form__swap">
          <PIconButton icon="swap" variant="tonal" :label="t('finance.form.swap')" @click="swap" />
        </div>
        <PField :label="t('finance.form.to')" :error="errors.destination_account_id">
          <PSelect v-model="toId" :options="accountOptions" />
        </PField>
        <div class="form__row">
          <PField :label="t('finance.form.date')" :error="errors.occurred_on">
            <PDateInput v-model="day" />
          </PField>
          <PField :label="t('finance.form.time')" optional>
            <PDateInput v-model="time" type="time" />
          </PField>
        </div>
        <PText variant="sm" tone="muted">{{ t('finance.form.transferHint') }}</PText>
      </template>
    </form>
    <template #footer>
      <PCheckbox v-if="!editing" v-model="another" class="form__footer-start">{{
        t('finance.form.createAnother')
      }}</PCheckbox>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="transaction-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!accounts.length"
        >{{ submitLabel }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
