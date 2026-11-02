<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { dateShort, km, money, monthName } from '@/lib/format'
import { PButton, PEmptyState, PQueryState, PStatCard, useToast } from '@/ui'

import { useArchiveVehicle, useOverview, useVehicles, type Vehicle } from '../api'
import VehicleCard from '../components/VehicleCard.vue'
import FuelingDialog from '../forms/FuelingDialog.vue'
import UpdateKmDialog from '../forms/UpdateKmDialog.vue'
import VehicleDialog from '../forms/VehicleDialog.vue'

const { t, te } = useI18n()
const toast = useToast()
const vehicles = useVehicles()
const overview = useOverview()
const archive = useArchiveVehicle()

const kmFor = ref<string | null>(null)
const fuelFor = ref<string | null>(null)
const editing = ref<Vehicle | null>(null)
const creating = ref(false)

const month = computed(() =>
  overview.data.value ? monthName(`${overview.data.value.month}-01`) : '',
)
const kmCaption = computed(() =>
  (overview.data.value?.vehicles_km ?? [])
    .map((item) => `${item.vehicle.name}: ${km(item.km).replace(' km', '')}`)
    .join(' · '),
)
const nextDue = computed(() => {
  const due = overview.data.value?.next_due
  if (!due) return null
  const value =
    due.primary === 'km' && due.remaining_km !== null
      ? km(due.remaining_km)
      : t('garage.oil.days', due.remaining_days ?? 0)
  const when = due.due_on ? ` · ≈ ${dateShort(due.due_on)}` : ''
  return {
    value,
    caption: `${t('garage.overview.nextDueOil', { vehicle: due.vehicle.name })}${when}`,
  }
})

async function doArchive(vehicle: Vehicle) {
  try {
    await archive.mutateAsync({ id: vehicle.id, archived: true })
    toast.show({ title: t('garage.form.archivedToast') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

const openKm = computed({ get: () => kmFor.value !== null, set: (v) => !v && (kmFor.value = null) })
const openFuel = computed({
  get: () => fuelFor.value !== null,
  set: (v) => !v && (fuelFor.value = null),
})
const openEdit = computed({
  get: () => editing.value !== null,
  set: (v) => !v && (editing.value = null),
})
</script>

<template>
  <PQueryState
    :loading="vehicles.isPending.value"
    :error="vehicles.error.value"
    :empty="(vehicles.data.value ?? []).length === 0"
    @retry="vehicles.refetch()"
  >
    <template #empty>
      <PEmptyState
        variant="card"
        icon="car"
        tone="garage"
        :title="t('garage.empty.title')"
        :description="t('garage.empty.description')"
      >
        <PButton variant="primary" icon="add" @click="creating = true">{{
          t('garage.empty.action')
        }}</PButton>
      </PEmptyState>
    </template>

    <div v-if="overview.data.value" class="tab__stats">
      <PStatCard
        :label="t('garage.overview.fuel', { month })"
        :value="money(overview.data.value.month_fuel_cents)"
        :caption="t('garage.overview.fuelings', overview.data.value.month_fuelings_count)"
      />
      <PStatCard
        :label="t('garage.overview.km', { month })"
        :value="km(overview.data.value.month_km)"
        :caption="kmCaption"
      />
      <PStatCard
        :label="t('garage.overview.nextDue')"
        :value="nextDue?.value ?? t('garage.overview.noNextDue')"
        :caption="nextDue?.caption"
      />
    </div>

    <div class="tab__grid">
      <VehicleCard
        v-for="vehicle in vehicles.data.value"
        :key="vehicle.id"
        :vehicle="vehicle"
        @update-km="kmFor = vehicle.id"
        @fuel="fuelFor = vehicle.id"
        @edit="editing = vehicle"
        @archive="doArchive(vehicle)"
      />
    </div>
    <PButton variant="dashed" icon="add" @click="creating = true">{{
      t('garage.actions.addVehicle')
    }}</PButton>
  </PQueryState>

  <UpdateKmDialog v-model:open="openKm" :vehicle-id="kmFor ?? undefined" />
  <FuelingDialog v-model:open="openFuel" :vehicle-id="fuelFor ?? undefined" />
  <VehicleDialog v-model:open="openEdit" :vehicle="editing ?? undefined" />
  <VehicleDialog v-model:open="creating" />
</template>

<style scoped>
.tab__stats {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
}

.tab__grid {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(420px, 100%), 1fr));
}
</style>
