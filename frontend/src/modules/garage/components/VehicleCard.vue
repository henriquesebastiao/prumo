<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, decimal, integer, liters, money, relativeDateTime } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PIconButton,
  PLink,
  PMenu,
  PText,
  PTile,
  type MenuEntry,
} from '@/ui'

import type { Vehicle } from '../api'
import { vehicleIcon } from '../helpers'
import OilPanel from './OilPanel.vue'

const props = defineProps<{ vehicle: Vehicle }>()
const emit = defineEmits<{ updateKm: []; fuel: []; edit: []; archive: [] }>()
const { t } = useI18n()
const to = computed(() => ({ name: 'garage.vehicle', params: { vehicleId: props.vehicle.id } }))
const menu = computed<MenuEntry[]>(() => [
  { label: t('garage.actions.edit'), icon: 'edit', onSelect: () => emit('edit') },
  { label: t('garage.actions.archive'), icon: 'page', onSelect: () => emit('archive') },
])
const last = computed(() => props.vehicle.stats.last_fueling)
</script>

<template>
  <PCard as="article" class="vehicle">
    <template #header>
      <PTile :icon="vehicleIcon(vehicle.kind)" tone="garage" size="lg" />
      <div class="vehicle__title">
        <PText variant="heading" as="h2">{{ vehicle.name }}</PText>
        <div class="vehicle__chips">
          <PBadge>{{ t(`garage.kind.${vehicle.kind}`) }}</PBadge>
          <PBadge>{{ vehicle.year }}</PBadge>
        </div>
      </div>
      <PMenu :items="menu">
        <template #trigger><PIconButton icon="more" :label="t('garage.actions.more')" /></template>
      </PMenu>
    </template>

    <div class="vehicle__km">
      <div>
        <PText variant="sm" tone="muted">{{ t('garage.vehicle.currentKm') }}</PText>
        <PText variant="number-xl"
          >{{ integer(vehicle.current_km) }}<small> {{ t('garage.units.km') }}</small></PText
        >
        <PText variant="sm" tone="muted">{{
          t('garage.vehicle.updated', {
            when: relativeDateTime(vehicle.current_km_at).toLocaleLowerCase(),
          })
        }}</PText>
      </div>
      <div v-if="vehicle.stats.avg_consumption_km_l" class="vehicle__consumption">
        <PText variant="sm" tone="muted">{{ t('garage.vehicle.avgConsumption') }}</PText>
        <PText variant="strong">{{
          t('garage.vehicle.kmL', { value: decimal(vehicle.stats.avg_consumption_km_l) })
        }}</PText>
      </div>
    </div>

    <OilPanel v-if="vehicle.oil_change" :oil="vehicle.oil_change" />

    <PText variant="sm" tone="secondary">{{
      last
        ? t('garage.vehicle.lastFueling', {
            date: dateShort(last.fueled_at),
            liters: liters(last.volume_ml),
            total: money(last.total_cents),
          })
        : t('garage.vehicle.noFueling')
    }}</PText>

    <div class="vehicle__actions">
      <PButton variant="primary" @click="emit('updateKm')">{{
        t('garage.actions.updateKm')
      }}</PButton>
      <PButton @click="emit('fuel')">{{ t('garage.actions.fuel') }}</PButton>
      <PLink :to="to" class="vehicle__link">{{ t('garage.actions.details') }}</PLink>
    </div>
  </PCard>
</template>

<style scoped>
.vehicle__title {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: var(--space-1-5);
}

.vehicle__chips,
.vehicle__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.vehicle__km {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-3);
}

.vehicle__consumption {
  text-align: right;
}

.vehicle__link {
  margin-left: auto;
}
</style>
