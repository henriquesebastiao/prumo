<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { date, dateTime, km, money } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PConfirmDialog,
  PDateBadge,
  PDescriptionList,
  PList,
  PListItem,
  PQueryState,
  PTable,
  PText,
  PTile,
  useToast,
} from '@/ui'

import { useDeleteMaintenance, useMaintenance, useMaintenances } from '../api'
import MaintenanceDialog from '../forms/MaintenanceDialog.vue'

const props = defineProps<{ vehicleId: string; maintenanceId: string }>()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const query = useMaintenance(
  () => props.vehicleId,
  () => props.maintenanceId,
)
const m = computed(() => query.data.value)
const remove = useDeleteMaintenance()
const editOpen = ref(false)
const deleteOpen = ref(false)

const sameWorkshop = useMaintenances(() => ({ workshop_id: m.value?.workshop?.id ?? 'none' }), 6)
const others = computed(() =>
  (sameWorkshop.data.value?.pages[0]?.items ?? [])
    .filter((item) => item.id !== props.maintenanceId)
    .slice(0, 5),
)

const rows = computed(() => {
  if (!m.value) return []
  const items = m.value.items.map((item) => ({
    id: item.id,
    description: item.quantity > 1 ? `${item.description} × ${item.quantity}` : item.description,
    type: t('garage.maintenance.part'),
    value: item.total_cents,
  }))
  if (m.value.labor_cost_cents)
    items.push({
      id: 'labor',
      description: t('garage.maintenance.laborTotal'),
      type: t('garage.maintenance.service'),
      value: m.value.labor_cost_cents,
    })
  return items
})
const columns = computed(() => [
  { key: 'description', label: t('garage.maintenance.item') },
  { key: 'type', label: t('garage.maintenance.type') },
  { key: 'value', label: t('garage.maintenance.value'), align: 'end' as const },
])
const record = computed(() =>
  m.value
    ? [
        { label: t('garage.maintenance.vehicle'), value: m.value.vehicle.name },
        { label: t('garage.maintenance.dateTime'), value: dateTime(m.value.performed_at) },
        { label: t('garage.maintenance.kmAt'), value: km(m.value.km) },
        {
          label: t('garage.maintenance.workshop'),
          value: m.value.workshop?.name ?? t('garage.maintenance.noWorkshop'),
        },
      ]
    : [],
)
const totals = computed(() =>
  m.value
    ? [
        { label: t('garage.maintenance.partsTotal'), value: money(m.value.parts_cents) },
        { label: t('garage.maintenance.laborTotal'), value: money(m.value.labor_cost_cents) },
        { label: t('garage.maintenance.total'), value: money(m.value.total_cents) },
      ]
    : [],
)

async function destroy() {
  await remove.mutateAsync({ vehicleId: props.vehicleId, id: props.maintenanceId })
  deleteOpen.value = false
  toast.show({ title: t('garage.maintenance.deleted') })
  await router.push({ name: 'garage.vehicle', params: { vehicleId: props.vehicleId } })
}
</script>

<template>
  <div>
    <PButton :to="{ name: 'garage.vehicle', params: { vehicleId } }" icon="chevron-left">{{
      m?.vehicle.name ?? t('garage.vehicle.back')
    }}</PButton>
  </div>
  <PQueryState :loading="query.isPending.value" :error="query.error.value" @retry="query.refetch()">
    <template v-if="m">
      <PCard>
        <div class="maintenance__top">
          <PTile :icon="m.kind === 'oil_change' ? 'droplet' : 'wrench'" tone="garage" size="lg" />
          <div class="maintenance__title">
            <PText variant="overline">{{
              t('garage.maintenance.titleOf', { vehicle: m.vehicle.name })
            }}</PText>
            <PText variant="h1" as="h1">{{
              m.workshop?.name ?? t('garage.maintenance.title')
            }}</PText>
            <div class="maintenance__chips">
              <PBadge>{{ dateTime(m.performed_at) }}</PBadge>
              <PBadge>{{ km(m.km) }}</PBadge>
              <PBadge>{{ t('garage.maintenance.items', m.items.length) }}</PBadge>
            </div>
          </div>
          <div class="maintenance__total">
            <PText variant="sm" tone="muted">{{ t('garage.maintenance.total') }}</PText>
            <PText variant="number-xl">{{ money(m.total_cents) }}</PText>
          </div>
          <div class="maintenance__actions">
            <PButton icon="edit" @click="editOpen = true">{{ t('garage.actions.edit') }}</PButton>
            <PButton variant="ghost" icon="trash" @click="deleteOpen = true">{{
              t('garage.actions.delete')
            }}</PButton>
          </div>
        </div>
      </PCard>

      <div class="maintenance__split">
        <div class="maintenance__wide">
          <PCard :title="t('garage.maintenance.parts')">
            <PTable :columns="columns" :rows="rows" :row-key="(row) => row.id">
              <template #cell-type="{ row }">
                <PBadge :variant="row.id === 'labor' ? 'dashed' : 'soft'">{{ row.type }}</PBadge>
              </template>
              <template #cell-value="{ row }">{{ money(row.value) }}</template>
            </PTable>
            <PDescriptionList :items="totals" />
          </PCard>
          <PCard
            v-if="m.notes || m.oil_type"
            :title="m.oil_type ? t('garage.oil.oilType') : t('garage.maintenance.notes')"
          >
            <PText v-if="m.oil_type" variant="h3">{{ m.oil_type }}</PText>
            <PText v-if="m.notes" tone="secondary">{{ m.notes }}</PText>
          </PCard>
        </div>
        <div class="maintenance__side">
          <PCard :title="t('garage.maintenance.record')">
            <PDescriptionList :items="record" />
          </PCard>
          <PCard
            v-if="m.workshop && others.length"
            :title="t('garage.maintenance.sameWorkshop')"
            :link-label="t('garage.maintenance.seeAll')"
            :to="{ name: 'garage.maintenances' }"
          >
            <PList>
              <PListItem
                v-for="other in others"
                :key="other.id"
                :to="{
                  name: 'garage.maintenance',
                  params: { vehicleId: other.vehicle.id, maintenanceId: other.id },
                }"
                :title="
                  other.items.map((item) => item.description).join(', ') ||
                  t('garage.maintenance.title')
                "
                :subtitle="`${km(other.km)} · ${t('garage.maintenance.items', other.items.length)} · ${date(other.performed_at)}`"
              >
                <template #leading><PDateBadge :date="other.performed_at" /></template>
                <template #trailing>
                  <PText variant="h3" as="span">{{ money(other.total_cents) }}</PText>
                </template>
              </PListItem>
            </PList>
          </PCard>
        </div>
      </div>

      <MaintenanceDialog
        v-if="m.kind === 'general'"
        v-model:open="editOpen"
        :vehicle-id="vehicleId"
        :maintenance="m"
      />
      <PConfirmDialog
        v-model:open="deleteOpen"
        :title="t('garage.maintenance.deleteTitle')"
        :description="
          t('garage.maintenance.deleteDescription', {
            date: date(m.performed_at),
            total: money(m.total_cents),
          })
        "
        :confirm-label="t('garage.actions.delete')"
        :loading="remove.isPending.value"
        @confirm="destroy"
      />
    </template>
  </PQueryState>
</template>

<style scoped>
.maintenance__top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4) var(--space-5);
}

.maintenance__title {
  display: flex;
  min-width: 0;
  flex: 1 1 280px;
  flex-direction: column;
  gap: var(--space-1-5);
}

.maintenance__chips,
.maintenance__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.maintenance__split {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
}

.maintenance__wide,
.maintenance__side {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
}

.maintenance__wide {
  flex: 3 1 520px;
}

.maintenance__side {
  flex: 2 1 320px;
}
</style>
