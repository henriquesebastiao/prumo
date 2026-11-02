<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { date, km, money } from '@/lib/format'
import { PButton, PCard, PEmptyState, PQueryState, PTable, PText } from '@/ui'

import { useMaintenances, type Maintenance } from '../api'

const props = defineProps<{ kind: 'general' | 'oil_change' }>()
const { t } = useI18n()
const router = useRouter()
const query = useMaintenances(() => ({ kind: props.kind }))
const rows = computed<Maintenance[]>(
  () => query.data.value?.pages.flatMap((page) => page.items) ?? [],
)
const total = computed(() => query.data.value?.pages[0]?.total ?? 0)
const oil = computed(() => props.kind === 'oil_change')

const columns = computed(() => [
  { key: 'date', label: t('garage.lists.date') },
  { key: 'vehicle', label: t('garage.lists.vehicle') },
  { key: 'km', label: t('garage.lists.km'), align: 'end' as const },
  oil.value
    ? { key: 'oil', label: t('garage.lists.oil') }
    : { key: 'workshop', label: t('garage.lists.workshop') },
  oil.value
    ? { key: 'next', label: t('garage.lists.next') }
    : { key: 'items', label: t('garage.lists.items') },
  { key: 'total', label: t('garage.lists.total'), align: 'end' as const },
])

function nextChange(row: Maintenance): string {
  const parts = [
    row.next_oil_change_km !== null ? km(row.next_oil_change_km) : null,
    row.next_oil_change_on ? date(row.next_oil_change_on) : null,
  ].filter(Boolean)
  return parts.length ? parts.join(` ${t('garage.oil.or')} `) : '—'
}

function open(row: Maintenance) {
  void router.push({
    name: 'garage.maintenance',
    params: { vehicleId: row.vehicle.id, maintenanceId: row.id },
  })
}
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
        <PEmptyState
          :icon="oil ? 'droplet' : 'wrench'"
          tone="garage"
          :title="t(oil ? 'garage.lists.emptyOilChanges' : 'garage.lists.emptyMaintenances')"
        />
      </template>
      <PTable :columns="columns" :rows="rows" :row-key="(row) => row.id">
        <template #cell-date="{ row }">{{ date(row.performed_at) }}</template>
        <template #cell-vehicle="{ row }">
          <PText variant="h3" as="span">{{ row.vehicle.name }}</PText>
        </template>
        <template #cell-km="{ row }">{{ km(row.km) }}</template>
        <template #cell-workshop="{ row }">{{
          row.workshop?.name ?? t('garage.maintenance.noWorkshop')
        }}</template>
        <template #cell-oil="{ row }">{{ row.oil_type ?? '—' }}</template>
        <template #cell-items="{ row }">{{
          row.items.map((item) => item.description).join(', ') || '—'
        }}</template>
        <template #cell-next="{ row }">{{ nextChange(row) }}</template>
        <template #cell-total="{ row }">
          <PButton variant="ghost" icon-right="chevron-right" @click="open(row)">{{
            money(row.total_cents)
          }}</PButton>
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
