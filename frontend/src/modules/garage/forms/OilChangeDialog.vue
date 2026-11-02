<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { date, decimal, integer, km, zonedToIso } from '@/lib/format'
import {
  PAlert,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PInput,
  PNote,
  PNumberInput,
  PPanel,
  PText,
  useToast,
} from '@/ui'

import { useOilSuggestion, useSaveMaintenance } from '../api'
import VehiclePicker from '../components/VehiclePicker.vue'
import { nowFields, useFormErrors, useVehicleChoice } from './useGarageForm'

const props = defineProps<{ vehicleId?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const toast = useToast()
const save = useSaveMaintenance()
const { errors, failure, capture, clear } = useFormErrors()
const { vehicles, selectedId, selected } = useVehicleChoice(open, () => props.vehicleId)

const day = ref('')
const kmValue = ref<number | null>(null)
const oilType = ref('')
const nextKm = ref<number | null>(null)
const nextOn = ref('')
const touched = ref({ km: false, on: false })

function reset() {
  clear()
  day.value = nowFields().day
  kmValue.value = selected.value?.current_km ?? null
  oilType.value = ''
  touched.value = { km: false, on: false }
}
watch(open, (value) => value && reset(), { immediate: true })
watch(selectedId, () => {
  if (selected.value) kmValue.value = selected.value.current_km
  touched.value = { km: false, on: false }
})

const suggestion = useOilSuggestion(selectedId, kmValue, day)
watch(
  () => suggestion.data.value,
  (value) => {
    if (!value) return
    if (!touched.value.km) nextKm.value = value.next_oil_change_km
    if (!touched.value.on) nextOn.value = value.next_oil_change_on ?? ''
    if (!oilType.value && value.previous_oil_types[0]) oilType.value = value.previous_oil_types[0]
  },
)

const interval = computed(() => {
  const vehicle = selected.value
  if (!vehicle) return ''
  const parts = [
    vehicle.oil_interval_km ? km(vehicle.oil_interval_km) : null,
    vehicle.oil_interval_months ? t('garage.oil.months', vehicle.oil_interval_months) : null,
  ].filter(Boolean)
  return parts.join(` ${t('garage.oil.or')} `)
})
const subtitle = computed(() =>
  selected.value && interval.value
    ? t('garage.form.intervalSubtitle', { vehicle: selected.value.name, interval: interval.value })
    : selected.value?.name,
)
const paceNote = computed(() => {
  const value = suggestion.data.value
  if (!value?.pace_km_per_day || !value.estimated_km_on) return null
  return t('garage.oil.pace', {
    pace: decimal(value.pace_km_per_day, 0),
    date: date(value.estimated_km_on),
  })
})

async function submit() {
  if (!selected.value || kmValue.value === null) return
  try {
    await save.mutateAsync({
      vehicleId: selected.value.id,
      body: {
        kind: 'oil_change',
        performed_at: zonedToIso(day.value, nowFields().time),
        km: kmValue.value,
        oil_type: oilType.value.trim() || null,
        next_oil_change_km: nextKm.value,
        next_oil_change_on: nextOn.value || null,
      },
    })
    toast.show({ title: t('garage.form.oilChangeSaved') })
    open.value = false
  } catch (error) {
    capture(error)
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('garage.form.oilChange')"
    :description="subtitle"
    icon="droplet"
    tone="garage"
  >
    <form id="oil-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="vehicles.length === 0" tone="secondary">{{ t('garage.form.noVehicles') }}</PText>
      <VehiclePicker v-if="!vehicleId" v-model="selectedId" :vehicles="vehicles" />
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('garage.form.date')" :error="errors.performed_at">
          <PDateInput v-model="day" />
        </PField>
        <PField :label="t('garage.form.km')" :error="errors.km">
          <PNumberInput v-model="kmValue" suffix="km" />
        </PField>
      </div>
      <PField :label="t('garage.form.oilType')" :error="errors.oil_type">
        <PInput v-model="oilType" :maxlength="120" />
      </PField>
      <div v-if="suggestion.data.value?.previous_oil_types.length" class="form__chips">
        <PText variant="sm" tone="muted" as="span">{{ t('garage.form.usedBefore') }}</PText>
        <PButton
          v-for="oil in suggestion.data.value.previous_oil_types"
          :key="oil"
          variant="chip"
          @click="oilType = oil"
          >{{ oil }}</PButton
        >
      </div>
      <PPanel class="form__stack">
        <div class="form__switch">
          <PText variant="h3" as="span">{{ t('garage.form.nextChange') }}</PText>
          <PText variant="sm" tone="muted" as="span">{{ t('garage.form.fromInterval') }}</PText>
        </div>
        <div class="form__row">
          <PField
            :label="t('garage.form.nextByKm')"
            :hint="
              selected?.oil_interval_km && kmValue !== null
                ? t('garage.form.nextKmHint', {
                    km: integer(kmValue),
                    interval: km(selected.oil_interval_km),
                  })
                : undefined
            "
            :error="errors.next_oil_change_km"
          >
            <PNumberInput v-model="nextKm" suffix="km" @update:model-value="touched.km = true" />
          </PField>
          <PField
            :label="t('garage.form.nextByDate')"
            :hint="
              selected?.oil_interval_months && day
                ? t('garage.form.nextDateHint', {
                    date: date(day),
                    months: t('garage.oil.months', selected.oil_interval_months),
                  })
                : undefined
            "
            :error="errors.next_oil_change_on"
          >
            <PDateInput v-model="nextOn" @update:model-value="touched.on = true" />
          </PField>
        </div>
      </PPanel>
      <PNote v-if="paceNote">{{ paceNote }}</PNote>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="oil-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!selected"
        >{{ t('garage.form.saveOilChange') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
