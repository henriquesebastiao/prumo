<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date, decimal, km, liters, money, relativeDateTime } from '@/lib/format'
import {
  PBadge,
  PCard,
  PDateBadge,
  PDivider,
  PIcon,
  PIconButton,
  PList,
  PListItem,
  PMenu,
  PSelect,
  PTabPanel,
  PTabs,
  PText,
  useToast,
  type MenuEntry,
} from '@/ui'

import {
  useDeleteFueling,
  useDeleteReading,
  useFuelings,
  useMaintenances,
  useReadings,
  type Fueling,
  type Maintenance,
  type Vehicle,
} from '../api'

const props = defineProps<{ vehicle: Vehicle }>()
const emit = defineEmits<{ editFueling: [fueling: Fueling] }>()
const { t, te } = useI18n()
const toast = useToast()

const maintenances = useMaintenances(() => ({ vehicle_id: props.vehicle.id }), 200)
const fuelings = useFuelings(() => ({ vehicle_id: props.vehicle.id }), 200)
const readings = useReadings(() => props.vehicle.id)
const deleteFueling = useDeleteFueling()
const deleteReading = useDeleteReading()

const tab = ref<'maintenances' | 'fuelings' | 'oil' | 'km'>('maintenances')
const year = ref(String(new Date().getFullYear()))

const allMaintenances = computed(
  () => maintenances.data.value?.pages.flatMap((page) => page.items) ?? [],
)
const allFuelings = computed(() => fuelings.data.value?.pages.flatMap((page) => page.items) ?? [])
const yearOf = (value: string) => date(value).slice(-4)
const inYear = (value: string) => year.value === 'all' || yearOf(value) === year.value

const general = computed(() =>
  allMaintenances.value.filter((m) => m.kind === 'general' && inYear(m.performed_at)),
)
const oilChanges = computed(() =>
  allMaintenances.value.filter((m) => m.kind === 'oil_change' && inYear(m.performed_at)),
)
const fuelingRows = computed(() => allFuelings.value.filter((f) => inYear(f.fueled_at)))
const readingRows = computed(() => (readings.data.value ?? []).filter((r) => inYear(r.recorded_at)))

const years = computed(() => {
  const all = new Set<string>([
    ...allMaintenances.value.map((m) => yearOf(m.performed_at)),
    ...allFuelings.value.map((f) => yearOf(f.fueled_at)),
    ...(readings.data.value ?? []).map((r) => yearOf(r.recorded_at)),
  ])
  return [
    { value: 'all', label: t('garage.history.allYears') },
    ...[...all]
      .sort()
      .reverse()
      .map((value) => ({ value, label: value })),
  ]
})

const tabs = computed(() => [
  {
    value: 'maintenances' as const,
    label: t('garage.history.maintenances'),
    count: general.value.length,
  },
  {
    value: 'fuelings' as const,
    label: t('garage.history.fuelings'),
    count: fuelingRows.value.length,
  },
  { value: 'oil' as const, label: t('garage.history.oilChanges'), count: oilChanges.value.length },
  { value: 'km' as const, label: t('garage.history.km'), count: readingRows.value.length },
])

const generalTotal = computed(() => general.value.reduce((sum, m) => sum + m.total_cents, 0))

function maintenanceTitle(m: Maintenance): string {
  return m.workshop?.name ?? t('garage.maintenance.noWorkshop')
}
function maintenanceTo(m: Maintenance) {
  return {
    name: 'garage.maintenance',
    params: { vehicleId: props.vehicle.id, maintenanceId: m.id },
  }
}
function nextOf(m: Maintenance): string {
  return [
    m.next_oil_change_km !== null ? km(m.next_oil_change_km) : null,
    m.next_oil_change_on ? date(m.next_oil_change_on) : null,
  ]
    .filter(Boolean)
    .join(` ${t('garage.oil.or')} `)
}

function fuelingMenu(fueling: Fueling): MenuEntry[] {
  return [
    { label: t('garage.actions.edit'), icon: 'edit', onSelect: () => emit('editFueling', fueling) },
    {
      label: t('garage.actions.delete'),
      icon: 'trash',
      danger: true,
      onSelect: () =>
        deleteFueling
          .mutateAsync({ vehicleId: props.vehicle.id, id: fueling.id })
          .catch((error: unknown) =>
            toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' }),
          ),
    },
  ]
}

async function removeReading(id: string) {
  try {
    await deleteReading.mutateAsync({ vehicleId: props.vehicle.id, id })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <PCard>
    <PTabs v-model="tab" :items="tabs" :label="t('garage.history.label')">
      <template #start>
        <PText variant="h2" as="h2">{{ t('garage.history.title') }}</PText>
      </template>
      <template #end>
        <div class="history__year"><PSelect v-model="year" :options="years" /></div>
      </template>
      <PTabPanel value="maintenances">
        <PList v-if="general.length">
          <PListItem v-for="m in general" :key="m.id" :to="maintenanceTo(m)">
            <template #leading><PDateBadge :date="m.performed_at" /></template>
            <span class="history__body">
              <span>
                <PText variant="h3" as="span">{{ maintenanceTitle(m) }}</PText>
                <PText variant="sm" tone="muted" as="span">
                  · {{ date(m.performed_at) }} · {{ km(m.km) }}</PText
                >
              </span>
              <span class="history__chips">
                <PBadge v-for="item in m.items" :key="item.id" variant="tag"
                  >{{ item.description }} · <b>{{ money(item.total_cents) }}</b></PBadge
                >
                <PBadge v-if="m.labor_cost_cents" variant="dashed"
                  >{{ t('garage.history.labor') }} · {{ money(m.labor_cost_cents) }}</PBadge
                >
              </span>
            </span>
            <template #trailing>
              <PText variant="strong" as="span">{{ money(m.total_cents) }}</PText>
              <PIcon name="chevron-right" size="sm" />
            </template>
          </PListItem>
        </PList>
        <PText v-else variant="sm" tone="muted">{{ t('garage.history.empty') }}</PText>
        <PDivider v-if="general.length" class="history__divider" />
        <div v-if="general.length" class="history__footer">
          <PText variant="sm" tone="muted">{{
            t('garage.history.summary', { year: year === 'all' ? '' : year }, general.length)
          }}</PText>
          <PText variant="sm">{{
            t('garage.history.total', { value: money(generalTotal) })
          }}</PText>
        </div>
      </PTabPanel>

      <PTabPanel value="fuelings">
        <PList v-if="fuelingRows.length">
          <PListItem
            v-for="f in fuelingRows"
            :key="f.id"
            :title="`${t(`garage.fuel.${f.fuel_type}`)} · ${liters(f.volume_ml)}`"
            :subtitle="
              [
                km(f.km),
                t('garage.stats.pricePerLiter', {
                  price: money(Math.round(f.price_per_liter * 100)),
                }),
                f.consumption_km_l
                  ? t('garage.vehicle.kmL', { value: decimal(f.consumption_km_l) })
                  : t(f.full_tank ? 'garage.stats.fullTank' : 'garage.stats.partialTank'),
              ].join(' · ')
            "
          >
            <template #leading><PDateBadge :date="f.fueled_at" /></template>
            <template #trailing>
              <PText variant="strong" as="span">{{ money(f.total_cents) }}</PText>
              <PMenu :items="fuelingMenu(f)">
                <template #trigger
                  ><PIconButton icon="more" :label="t('garage.actions.more')"
                /></template>
              </PMenu>
            </template>
          </PListItem>
        </PList>
        <PText v-else variant="sm" tone="muted">{{ t('garage.history.empty') }}</PText>
      </PTabPanel>

      <PTabPanel value="oil">
        <PList v-if="oilChanges.length">
          <PListItem
            v-for="m in oilChanges"
            :key="m.id"
            :to="maintenanceTo(m)"
            :title="m.oil_type ?? t('garage.oil.title')"
            :subtitle="
              [km(m.km), nextOf(m) ? `${t('garage.lists.next')}: ${nextOf(m)}` : '']
                .filter(Boolean)
                .join(' · ')
            "
          >
            <template #leading><PDateBadge :date="m.performed_at" /></template>
            <template #trailing>
              <PText variant="strong" as="span">{{ money(m.total_cents) }}</PText>
            </template>
          </PListItem>
        </PList>
        <PText v-else variant="sm" tone="muted">{{ t('garage.history.empty') }}</PText>
      </PTabPanel>

      <PTabPanel value="km">
        <PList v-if="readingRows.length">
          <PListItem
            v-for="r in readingRows"
            :key="r.id"
            :title="km(r.km)"
            :subtitle="`${t(`garage.history.source.${r.source}`)} · ${relativeDateTime(r.recorded_at)}`"
          >
            <template #leading><PDateBadge :date="r.recorded_at" /></template>
            <template #trailing>
              <PIconButton
                v-if="r.source === 'manual' && readingRows.length > 1"
                icon="trash"
                :label="t('garage.history.deleteReading')"
                @click="removeReading(r.id)"
              />
            </template>
          </PListItem>
        </PList>
      </PTabPanel>
    </PTabs>
  </PCard>
</template>

<style scoped>
.history__year {
  width: 160px;
}

.history__body {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-1-5);
}

.history__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1-5);
}

.history__divider {
  margin: var(--space-2) 0 var(--space-3);
}

.history__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
}
</style>
