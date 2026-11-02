<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useRunQuickAction } from '@/app/quick-actions'
import {
  date as formatDate,
  dateShort,
  daysUntil,
  integer,
  km,
  money,
  monthName,
} from '@/lib/format'
import { PButton, PCard, PList, PListItem, PPanel, PProgress, PRing, PText } from '@/ui'

import type { GarageSummary } from '../api'

const props = defineProps<{ summary?: GarageSummary }>()
const { t } = useI18n()
const run = useRunQuickAction()
const next = computed(() => props.summary?.next_due ?? null)

const nextValue = computed(() => {
  const due = next.value
  if (!due) return { value: '', unit: '' }
  return due.primary === 'km'
    ? { value: integer(Math.abs(due.remaining_km ?? 0)), unit: 'km' }
    : { value: integer(Math.abs(due.remaining_days ?? 0)), unit: t('garage.oil.daysLeft') }
})
const nextWhen = computed(() => {
  const due = next.value
  if (!due) return ''
  if (due.status === 'overdue') return t('garage.widget.overdue')
  if (!due.due_on) return ''
  if (due.primary === 'km') {
    return t(
      'garage.widget.inDays',
      { date: dateShort(due.due_on) },
      Math.max(0, daysUntil(due.due_on)),
    )
  }
  return t('garage.widget.onDate', { date: formatDate(due.due_on) })
})

function rowValue(vehicle: GarageSummary['vehicles'][number]): string {
  if (vehicle.oil_primary === 'km' && vehicle.remaining_km !== null) return km(vehicle.remaining_km)
  if (vehicle.oil_primary === 'date' && vehicle.remaining_days !== null)
    return t('garage.oil.days', vehicle.remaining_days)
  return ''
}
function rowSubtitle(vehicle: GarageSummary['vehicles'][number]): string {
  const value = km(vehicle.current_km)
  if (vehicle.oil_primary === 'km') return t('garage.widget.byKm', { km: value })
  if (vehicle.oil_primary === 'date') return t('garage.widget.byDate', { km: value })
  return t('garage.widget.noOil', { km: value })
}
</script>

<template>
  <PCard
    as="article"
    :title="t('garage.nav')"
    :subtitle="t('garage.widget.count', summary?.vehicles_count ?? 0)"
    icon="car"
    tone="garage"
    :link-label="t('garage.actions.open')"
    :to="{ name: 'garage.home' }"
  >
    <PPanel v-if="next" class="widget__next">
      <PRing
        :value="next.used_percent ?? 0"
        :tone="next.status === 'overdue' ? 'danger' : 'garage'"
        :size="92"
      >
        <PText variant="number-l" as="span">{{ nextValue.value }}</PText>
        <PText variant="xs" weight="bold" tone="muted" as="span">{{ nextValue.unit }}</PText>
      </PRing>
      <div class="widget__stack">
        <PText variant="sm" tone="muted">{{ t('garage.widget.nextOil') }}</PText>
        <PText variant="strong">{{ next.vehicle.name }}</PText>
        <PText variant="sm" tone="secondary">{{ nextWhen }}</PText>
      </div>
    </PPanel>
    <PList v-if="summary?.vehicles.length">
      <PListItem
        v-for="vehicle in summary.vehicles"
        :key="vehicle.vehicle.id"
        :title="vehicle.vehicle.name"
        :subtitle="rowSubtitle(vehicle)"
        :to="{ name: 'garage.vehicle', params: { vehicleId: vehicle.vehicle.id } }"
      >
        <template #trailing>
          <PProgress
            v-if="vehicle.used_percent !== null"
            :value="vehicle.used_percent"
            :tone="vehicle.oil_status === 'overdue' ? 'danger' : 'garage'"
            size="sm"
            class="widget__bar"
          />
          <PText variant="h3" as="span" class="widget__value">{{ rowValue(vehicle) }}</PText>
        </template>
      </PListItem>
    </PList>
    <div class="widget__between">
      <PText variant="sm" tone="muted">{{
        t('garage.widget.monthFuel', { month: monthName(new Date()) })
      }}</PText>
      <PText variant="h3">{{ money(summary?.month_fuel_cents ?? 0) }}</PText>
    </div>
    <div class="widget__actions">
      <PButton variant="primary" @click="run('garage.update-km')">{{
        t('garage.actions.updateKm')
      }}</PButton>
      <PButton @click="run('garage.add-fueling')">{{ t('garage.actions.fuel') }}</PButton>
    </div>
  </PCard>
</template>

<style scoped>
.widget__next {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.widget__stack {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-0-5);
}

.widget__bar {
  width: 100px;
}

@media (width < 600px) {
  .widget__bar {
    width: 64px;
  }

  .widget__value {
    min-width: 0;
  }
}

.widget__value {
  min-width: 64px;
  text-align: right;
}

.widget__between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.widget__actions {
  display: grid;
  gap: var(--space-2);
  grid-template-columns: 1fr 1fr;
}
</style>
