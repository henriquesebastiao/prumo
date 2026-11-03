<script setup lang="ts">
/** "Saldo por conta": each account with a bar relative to the largest balance. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { money } from '@/lib/format'
import { PList, PListItem, PProgress, PText, PTile } from '@/ui'

import type { Schemas } from '@/lib/api/client'

import { dataIcon } from '../helpers'

const props = defineProps<{ balances: Schemas['AccountBalance'][] }>()
const { t } = useI18n()
const max = computed(() => Math.max(1, ...props.balances.map((item) => item.balance_cents)))
</script>

<template>
  <PList>
    <PListItem
      v-for="item in balances"
      :key="item.account.id"
      :title="item.account.name"
      :subtitle="t(`finance.accountKinds.${item.account.kind}`)"
    >
      <template #leading>
        <PTile :icon="dataIcon(item.account.icon, 'wallet')" tone="finance" />
      </template>
      <template #trailing>
        <span class="balances__bar">
          <PProgress
            :value="Math.max(0, item.balance_cents)"
            :max="max"
            tone="finance"
            :label="item.account.name"
          />
        </span>
        <PText variant="strong" as="span" class="balances__value">{{
          money(item.balance_cents)
        }}</PText>
      </template>
    </PListItem>
  </PList>
</template>

<style scoped>
.balances__bar {
  width: clamp(80px, 22vw, 280px);
}

.balances__value {
  min-width: 112px;
  text-align: right;
}

@media (width < 600px) {
  .balances__bar {
    display: none;
  }
}
</style>
