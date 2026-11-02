<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { date, decimal, km, liters, money } from '@/lib/format'
import { PButton, PCard, PEmptyState, PQueryState, PTable, PText } from '@/ui'

import { useFuelings, type Fueling } from '../api'

const { t } = useI18n()
const query = useFuelings({})
const rows = computed<Fueling[]>(() => query.data.value?.pages.flatMap((page) => page.items) ?? [])
const total = computed(() => query.data.value?.pages[0]?.total ?? 0)
const columns = computed(() => [
  { key: 'date', label: t('garage.lists.date') },
  { key: 'vehicle', label: t('garage.lists.vehicle') },
  { key: 'fuel', label: t('garage.lists.fuel') },
  { key: 'km', label: t('garage.lists.km'), align: 'end' as const },
  { key: 'liters', label: t('garage.lists.liters'), align: 'end' as const },
  { key: 'price', label: t('garage.lists.price'), align: 'end' as const },
  { key: 'consumption', label: t('garage.lists.consumption'), align: 'end' as const },
  { key: 'total', label: t('garage.lists.total'), align: 'end' as const },
])
</script>

<template>
  <PCard>
    <PQueryState
      :loading="query.isPending.value"
      :error="query.error.value"
      :empty="rows.length === 0"
      @retry="query.refetch()"
    >
      <template #empty>
        <PEmptyState icon="fuel" tone="garage" :title="t('garage.lists.emptyFuelings')" />
      </template>
      <PTable
        :columns="columns"
        :rows="rows"
        :row-key="(row) => row.id"
        :caption="t('garage.tabs.fuelings')"
      >
        <template #cell-date="{ row }">{{ date(row.fueled_at) }}</template>
        <template #cell-vehicle="{ row }">
          <PText variant="h3" as="span">{{ row.vehicle.name }}</PText>
        </template>
        <template #cell-fuel="{ row }">{{ t(`garage.fuel.${row.fuel_type}`) }}</template>
        <template #cell-km="{ row }">{{ km(row.km) }}</template>
        <template #cell-liters="{ row }">{{ liters(row.volume_ml) }}</template>
        <template #cell-price="{ row }">{{ decimal(row.price_per_liter, 3) }}</template>
        <template #cell-consumption="{ row }">{{
          row.consumption_km_l
            ? t('garage.vehicle.kmL', { value: decimal(row.consumption_km_l) })
            : '—'
        }}</template>
        <template #cell-total="{ row }">
          <PText variant="h3" as="span">{{ money(row.total_cents) }}</PText>
        </template>
      </PTable>
      <div class="list__footer">
        <PText variant="sm" tone="muted">{{
          t('garage.lists.showing', { shown: rows.length, total })
        }}</PText>
        <PButton
          v-if="query.hasNextPage.value"
          :loading="query.isFetchingNextPage.value"
          @click="query.fetchNextPage()"
          >{{ t('garage.lists.loadMore') }}</PButton
        >
      </div>
    </PQueryState>
  </PCard>
</template>

<style scoped>
.list__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
</style>
