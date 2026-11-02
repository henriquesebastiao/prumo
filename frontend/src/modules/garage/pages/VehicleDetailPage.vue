<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { dateShort, integer, liters, money, monthName, relativeDateTime } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PDivider,
  PIconButton,
  PConfirmDialog,
  PMenu,
  PPopover,
  PQueryState,
  PStatCard,
  PText,
  PTile,
  useToast,
  type MenuEntry,
} from '@/ui'

import { useRouter } from 'vue-router'

import { useArchiveVehicle, useDeleteVehicle, useVehicle, type Fueling } from '../api'
import ConsumptionCard from '../components/ConsumptionCard.vue'
import HistoryCard from '../components/HistoryCard.vue'
import OilCard from '../components/OilCard.vue'
import FuelingDialog from '../forms/FuelingDialog.vue'
import MaintenanceDialog from '../forms/MaintenanceDialog.vue'
import OilChangeDialog from '../forms/OilChangeDialog.vue'
import UpdateKmForm from '../forms/UpdateKmForm.vue'
import VehicleDialog from '../forms/VehicleDialog.vue'
import { vehicleIcon } from '../helpers'

const props = defineProps<{ vehicleId: string }>()
const { t, te } = useI18n()
const toast = useToast()
const query = useVehicle(() => props.vehicleId)
const vehicle = computed(() => query.data.value)
const archive = useArchiveVehicle()
const remove = useDeleteVehicle()
const router = useRouter()
const deleteOpen = ref(false)

async function destroy() {
  if (!vehicle.value) return
  await remove.mutateAsync(vehicle.value.id)
  deleteOpen.value = false
  toast.show({ title: t('garage.form.deleted') })
  await router.push({ name: 'garage.home' })
}

const kmOpen = ref(false)
const fuelingOpen = ref(false)
const editingFueling = ref<Fueling | undefined>()
const oilOpen = ref(false)
const maintenanceOpen = ref(false)
const editOpen = ref(false)

function openFueling(fueling?: Fueling) {
  editingFueling.value = fueling
  fuelingOpen.value = true
}

async function toggleArchive() {
  if (!vehicle.value) return
  const archived = !vehicle.value.archived_at
  try {
    await archive.mutateAsync({ id: vehicle.value.id, archived })
    toast.show({ title: t(archived ? 'garage.form.archivedToast' : 'garage.form.unarchivedToast') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

const menu = computed<MenuEntry[]>(() => [
  {
    label: t(vehicle.value?.archived_at ? 'garage.actions.unarchive' : 'garage.actions.archive'),
    icon: 'page',
    onSelect: () => void toggleArchive(),
  },
  {
    label: t('garage.actions.delete'),
    icon: 'trash',
    danger: true,
    onSelect: () => (deleteOpen.value = true),
  },
])

const month = computed(() => monthName(new Date()))
const last = computed(() => vehicle.value?.stats.last_fueling)
</script>

<template>
  <div>
    <PButton :to="{ name: 'garage.home' }" icon="chevron-left">{{
      t('garage.vehicle.back')
    }}</PButton>
  </div>
  <PQueryState :loading="query.isPending.value" :error="query.error.value" @retry="query.refetch()">
    <template v-if="vehicle">
      <PCard>
        <div class="detail__top">
          <PTile :icon="vehicleIcon(vehicle.kind)" tone="garage" size="lg" />
          <div class="detail__name">
            <PText variant="h1" as="h1">{{ vehicle.name }}</PText>
            <div class="detail__chips">
              <PBadge>{{ t(`garage.kind.${vehicle.kind}`) }}</PBadge>
              <PBadge>{{ vehicle.year }}</PBadge>
              <PBadge v-if="vehicle.fuel_type">{{
                t(`garage.fuelShort.${vehicle.fuel_type}`)
              }}</PBadge>
              <PBadge v-if="vehicle.archived_at" variant="outline">{{
                t('garage.vehicle.archived')
              }}</PBadge>
            </div>
          </div>
          <div class="detail__km">
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
          <PPopover
            v-model:open="kmOpen"
            side="bottom"
            align="end"
            :label="t('garage.actions.updateKm')"
          >
            <template #trigger>
              <PButton variant="primary" icon="gauge">{{ t('garage.actions.updateKm') }}</PButton>
            </template>
            <PText variant="h3">{{ t('garage.actions.updateKm') }}</PText>
            <UpdateKmForm
              :vehicle="vehicle"
              form-id="detail-km-form"
              show-actions
              @done="kmOpen = false"
              @cancel="kmOpen = false"
            />
          </PPopover>
        </div>
        <PDivider />
        <div class="detail__actions">
          <PButton variant="chip" icon="fuel" icon-tone="garage" @click="openFueling()">{{
            t('garage.actions.addFueling')
          }}</PButton>
          <PButton variant="chip" icon="droplet" icon-tone="garage" @click="oilOpen = true">{{
            t('garage.actions.addOilChange')
          }}</PButton>
          <PButton
            variant="chip"
            icon="wrench"
            icon-tone="garage"
            @click="maintenanceOpen = true"
            >{{ t('garage.actions.addMaintenance') }}</PButton
          >
          <PButton variant="chip" icon="edit" @click="editOpen = true">{{
            t('garage.actions.edit')
          }}</PButton>
          <PMenu :items="menu" align="start">
            <template #trigger>
              <PIconButton icon="more" variant="outline" :label="t('garage.actions.more')" />
            </template>
          </PMenu>
        </div>
      </PCard>

      <div class="detail__split">
        <OilCard
          :vehicle="vehicle"
          class="detail__wide"
          @register="oilOpen = true"
          @edit="editOpen = true"
        />
        <div class="detail__side">
          <ConsumptionCard :vehicle="vehicle" />
          <div class="detail__stats">
            <PStatCard
              :label="t('garage.stats.lastFueling')"
              :value="last ? money(last.total_cents) : '—'"
            >
              <template v-if="last" #caption>
                {{
                  t('garage.stats.lastFuelingCaption', {
                    date: dateShort(last.fueled_at),
                    liters: liters(last.volume_ml),
                  })
                }}
                <br />
                {{
                  t('garage.stats.pricePerLiter', {
                    price: money(Math.round(last.price_per_liter * 100)),
                  })
                }}
                · {{ t(last.full_tank ? 'garage.stats.fullTank' : 'garage.stats.partialTank') }}
              </template>
            </PStatCard>
            <PStatCard
              :label="t('garage.stats.monthSpent', { month })"
              :value="money(vehicle.stats.month_spent_cents)"
            >
              <template #caption>
                {{ t('garage.stats.fuelings', vehicle.stats.month_fuelings_count) }}
                <br />
                {{ t('garage.stats.maintenances', vehicle.stats.month_maintenances_count) }}
              </template>
            </PStatCard>
          </div>
        </div>
      </div>

      <HistoryCard :vehicle="vehicle" @edit-fueling="openFueling" />

      <FuelingDialog
        v-model:open="fuelingOpen"
        :vehicle-id="vehicle.id"
        :fueling="editingFueling"
      />
      <OilChangeDialog v-model:open="oilOpen" :vehicle-id="vehicle.id" />
      <MaintenanceDialog v-model:open="maintenanceOpen" :vehicle-id="vehicle.id" />
      <VehicleDialog v-model:open="editOpen" :vehicle="vehicle" />
      <PConfirmDialog
        v-model:open="deleteOpen"
        :title="t('garage.form.deleteVehicleTitle', { name: vehicle.name })"
        :description="t('garage.form.deleteVehicleDescription')"
        :confirm-label="t('garage.actions.delete')"
        :loading="remove.isPending.value"
        @confirm="destroy"
      />
    </template>
  </PQueryState>
</template>

<style scoped>
.detail__top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4) var(--space-5);
}

.detail__name {
  display: flex;
  min-width: 0;
  flex: 1 1 280px;
  flex-direction: column;
  gap: var(--space-2);
}

.detail__chips,
.detail__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.detail__split {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
}

.detail__wide {
  min-width: 0;
  flex: 3 1 520px;
}

.detail__side {
  display: flex;
  min-width: 0;
  flex: 2 1 340px;
  flex-direction: column;
  gap: var(--space-4);
}

.detail__stats {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
}
</style>
