<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { isoToZoned, km, money, moneyParts, relativeDateTime, zonedToIso } from '@/lib/format'
import {
  PAlert,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PInput,
  PMoneyInput,
  PNumberInput,
  PText,
  PTextarea,
  useToast,
} from '@/ui'

import { useSaveMaintenance, type Maintenance } from '../api'
import ItemsEditor from '../components/ItemsEditor.vue'
import VehiclePicker from '../components/VehiclePicker.vue'
import WorkshopField from '../components/WorkshopField.vue'
import type { ItemDraft, WorkshopChoice } from '../helpers'
import { nowFields, useFormErrors, useVehicleChoice } from './useGarageForm'

const props = defineProps<{ vehicleId?: string; maintenance?: Maintenance }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const toast = useToast()
const save = useSaveMaintenance()
const { errors, failure, capture, clear } = useFormErrors()
const { vehicles, selectedId, selected } = useVehicleChoice(
  open,
  () => props.maintenance?.vehicle.id ?? props.vehicleId,
)

const day = ref('')
const time = ref('')
const kmValue = ref<number | null>(null)
const workshop = ref<WorkshopChoice | null>(null)
const items = ref<ItemDraft[]>([])
const labor = ref<number | null>(null)
const notes = ref('')
let key = 0

function reset() {
  clear()
  const source = props.maintenance
  const when = source ? isoToZoned(source.performed_at) : nowFields()
  day.value = when.day
  time.value = when.time
  kmValue.value = source?.km ?? selected.value?.current_km ?? null
  workshop.value = source?.workshop ? { id: source.workshop.id } : null
  items.value = source
    ? source.items.map((item) => ({
        key: key++,
        description: item.description,
        quantity: item.quantity,
        unit_price_cents: item.unit_price_cents,
      }))
    : [{ key: key++, description: '', quantity: 1, unit_price_cents: null }]
  labor.value = source?.labor_cost_cents ?? null
  notes.value = source?.notes ?? ''
}
watch(open, (value) => value && reset(), { immediate: true })
watch(selectedId, () => {
  if (!props.maintenance && selected.value) kmValue.value = selected.value.current_km
})

const filledItems = computed(() => items.value.filter((item) => item.description.trim()))
/** Convenience total while typing (G4); the saved total comes from the API. */
const partsCents = computed(() =>
  filledItems.value.reduce(
    (sum, item) => sum + (item.quantity ?? 1) * (item.unit_price_cents ?? 0),
    0,
  ),
)
const totalCents = computed(() => partsCents.value + (labor.value ?? 0))
const lastHint = computed(() =>
  selected.value && !props.maintenance
    ? t('garage.form.lastReading', {
        km: km(selected.value.current_km),
        when: relativeDateTime(selected.value.current_km_at).toLocaleLowerCase(),
      })
    : undefined,
)

async function submit() {
  if (!selected.value || kmValue.value === null) return
  const body = {
    performed_at: zonedToIso(day.value, time.value),
    km: kmValue.value,
    labor_cost_cents: labor.value ?? 0,
    notes: notes.value.trim() || null,
    workshop_id: workshop.value?.id ?? null,
    workshop_name: workshop.value?.id ? null : (workshop.value?.name ?? null),
    items: filledItems.value.map((item) => ({
      description: item.description.trim(),
      quantity: item.quantity ?? 1,
      unit_price_cents: item.unit_price_cents ?? 0,
    })),
  }
  try {
    await save.mutateAsync({ vehicleId: selected.value.id, id: props.maintenance?.id, body })
    toast.show({ title: t('garage.form.maintenanceSaved') })
    open.value = false
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t(maintenance ? 'garage.form.editMaintenance' : 'garage.form.maintenance')"
    icon="wrench"
    tone="garage"
    size="l"
  >
    <form id="maintenance-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="vehicles.length === 0" tone="secondary">{{ t('garage.form.noVehicles') }}</PText>
      <VehiclePicker v-if="!vehicleId && !maintenance" v-model="selectedId" :vehicles="vehicles" />
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('garage.form.date')" :error="errors.performed_at">
          <PDateInput v-model="day" />
        </PField>
        <PField :label="t('garage.form.time')">
          <PDateInput v-model="time" type="time" />
        </PField>
        <PField :label="t('garage.form.kmAt')" :hint="lastHint" :error="errors.km">
          <PNumberInput v-model="kmValue" suffix="km" />
        </PField>
      </div>
      <PField :label="t('garage.form.workshop')" :error="errors.workshop_name">
        <WorkshopField v-model="workshop" />
      </PField>
      <PField :label="t('garage.form.parts')" label-as="span">
        <ItemsEditor v-model="items" :errors="errors" />
      </PField>
      <div class="form__row">
        <PField :label="t('garage.form.labor')" :error="errors.labor_cost_cents">
          <PMoneyInput v-model="labor" />
        </PField>
        <PField
          :label="t('garage.form.total')"
          :hint="t('garage.form.totalHint', { parts: money(partsCents), labor: money(labor ?? 0) })"
        >
          <PInput
            :model-value="moneyParts(totalCents).amount"
            :prefix="moneyParts(0).symbol"
            align="end"
            calculated
            readonly
          />
        </PField>
      </div>
      <PField :label="t('garage.form.notes')" optional>
        <PTextarea v-model="notes" :placeholder="t('garage.form.notesPlaceholder')" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="maintenance-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!selected"
        >{{ t('garage.form.saveMaintenance') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
