<script setup lang="ts">
/** An unpaid invoice: card, closing and due dates, amount and the available limit. */
import { useI18n } from 'vue-i18n'

import { dateShort, money } from '@/lib/format'
import { PBadge, PIcon, PPanel, PProgress, PText } from '@/ui'

import type { OpenInvoice } from '../api'

defineProps<{ item: OpenInvoice }>()
const { t } = useI18n()
</script>

<template>
  <PPanel class="invoice">
    <div class="invoice__head">
      <span class="invoice__card">
        <PIcon name="card" data-tone="finance" />
        <PText variant="h3" as="span">{{ item.card.name }}</PText>
      </span>
      <PBadge :tone="item.invoice.status === 'overdue' ? 'danger' : 'neutral'">{{
        t('finance.overview.closesDue', {
          closing: dateShort(item.invoice.closing_on),
          due: dateShort(item.invoice.due_on),
        })
      }}</PBadge>
    </div>
    <PText variant="number-l">{{ money(item.invoice.remaining_cents) }}</PText>
    <PProgress
      :value="item.limit_cents - item.available_limit_cents"
      :max="Math.max(1, item.limit_cents)"
      tone="finance"
      :label="t('finance.overview.available')"
    />
    <div class="invoice__foot">
      <PText variant="sm" tone="secondary" as="span">{{ t('finance.overview.available') }}</PText>
      <PText variant="sm" weight="bold" as="span">{{
        t('finance.overview.availableOf', {
          available: money(item.available_limit_cents),
          limit: money(item.limit_cents),
        })
      }}</PText>
    </div>
  </PPanel>
</template>

<style scoped>
.invoice {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.invoice__head,
.invoice__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.invoice__card {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
</style>
