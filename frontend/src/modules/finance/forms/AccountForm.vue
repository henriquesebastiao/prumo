<script setup lang="ts">
/** Side panel of the Contas tab: creates or edits an account. */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PAlert,
  PButton,
  PCard,
  PField,
  PIconButton,
  PIconPicker,
  PInput,
  PMoneyInput,
  PSegmented,
  PSwatchPicker,
  PSwitch,
  PText,
  useToast,
} from '@/ui'

import { useSaveAccount, type Account, type AccountKind } from '../api'
import {
  ACCOUNT_ICONS,
  ACCOUNT_KINDS,
  colorTone,
  iconOptions,
  swatchOptions,
  type FinanceColor,
} from '../helpers'
import { useFormErrors } from './useFinanceForm'

const props = defineProps<{ account?: Account }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const toast = useToast()
const save = useSaveAccount()
const { errors, failure, capture, clear } = useFormErrors()

/** Icon suggested for each kind (the API applies the same default). */
const KIND_ICONS: Record<AccountKind, string> = {
  checking: 'landmark',
  savings: 'vault',
  cash: 'wallet',
  investment: 'trending-up',
  other: 'wallet',
}

const name = ref('')
const kind = ref<AccountKind>('checking')
const balance = ref<number | null>(0)
const color = ref<FinanceColor>('blue')
const icon = ref('landmark')
const includeInTotal = ref(true)

function reset() {
  clear()
  const account = props.account
  name.value = account?.name ?? ''
  kind.value = account?.kind ?? 'checking'
  balance.value = account?.initial_balance_cents ?? 0
  color.value = (account?.color as FinanceColor | undefined) ?? 'blue'
  icon.value = account?.icon ?? KIND_ICONS[kind.value]
  includeInTotal.value = account?.include_in_total ?? true
}
watch(() => props.account, reset, { immediate: true })
watch(kind, (value, previous) => {
  if (icon.value === KIND_ICONS[previous]) icon.value = KIND_ICONS[value]
})

const initialColor = computed(() => props.account?.color)
/** The design offers four kinds; `other` shows up only for accounts that already use it. */
const kindOptions = computed(() =>
  ACCOUNT_KINDS.filter((value) => value !== 'other' || props.account?.kind === 'other').map(
    (value) => ({ value, label: t(`finance.accountKindsShort.${value}`) }),
  ),
)

async function submit() {
  const body = {
    name: name.value,
    kind: kind.value,
    initial_balance_cents: balance.value ?? 0,
    color: color.value,
    icon: icon.value,
    include_in_total: includeInTotal.value,
  }
  try {
    await save.mutateAsync({ id: props.account?.id, body })
    toast.show({ title: t('finance.accounts.saved') })
    emit('close')
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PCard
    as="form"
    :title="account ? t('finance.accounts.editTitle') : t('finance.accounts.newTitle')"
    novalidate
    @submit.prevent="submit"
  >
    <template #actions>
      <PIconButton icon="close" :label="t('finance.actions.close')" @click="emit('close')" />
    </template>
    <div class="form">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('finance.accounts.name')" :error="errors.name">
        <PInput
          v-model="name"
          :placeholder="t('finance.accounts.namePlaceholder')"
          :maxlength="60"
        />
      </PField>
      <PField :label="t('finance.accounts.kind')" label-as="span" :error="errors.kind">
        <PSegmented
          v-model="kind"
          :options="kindOptions"
          :label="t('finance.accounts.kind')"
          block
        />
      </PField>
      <PField
        :label="
          account ? t('finance.accounts.initialBalanceEdit') : t('finance.accounts.initialBalance')
        "
        :hint="
          account
            ? t('finance.accounts.initialBalanceEditHint')
            : t('finance.accounts.initialBalanceHint')
        "
        :error="errors.initial_balance_cents"
      >
        <PMoneyInput v-model="balance" />
      </PField>
      <PField :label="t('finance.accounts.color')" label-as="span">
        <PSwatchPicker
          v-model="color"
          :options="swatchOptions(t, initialColor)"
          :label="t('finance.accounts.color')"
        />
      </PField>
      <PField :label="t('finance.accounts.icon')" label-as="span">
        <PIconPicker
          v-model="icon"
          :options="iconOptions(ACCOUNT_ICONS, t, account?.icon)"
          :label="t('finance.accounts.icon')"
          :tone="colorTone(color)"
        />
      </PField>
      <div class="form__switch">
        <PText variant="sm" as="span">{{ t('finance.accounts.includeInTotal') }}</PText>
        <PSwitch v-model="includeInTotal" :label="t('finance.accounts.includeInTotal')" />
      </div>
      <div class="form__actions">
        <PButton @click="emit('close')">{{ t('ui.cancel') }}</PButton>
        <PButton type="submit" variant="primary" :loading="save.isPending.value">{{
          account ? t('ui.save') : t('finance.accounts.create')
        }}</PButton>
      </div>
    </div>
  </PCard>
</template>

<style src="./form.css" scoped></style>
