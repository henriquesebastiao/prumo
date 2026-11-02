<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { decimal, isoToZoned, km, moneyParts, relativeDateTime, zonedToIso } from '@/lib/format'
import {
  PAlert,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PInput,
  PMoneyInput,
  PNumberInput,
  PPanel,
  PSegmented,
  PSwitch,
  PText,
  useToast,
} from '@/ui'

import { useSaveFueling, type Fueling } from '../api'
import VehiclePicker from '../components/VehiclePicker.vue'
import { FUEL_TYPES, type FuelType } from '../helpers'
import { nowFields, useFormErrors, useVehicleChoice } from './useGarageForm'

const props = defineProps<{ vehicleId?: string; fueling?: Fueling }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const toast = useToast()
const save = useSaveFueling()
const { errors, failure, capture, clear } = useFormErrors()
const { vehicles, selectedId, selected } = useVehicleChoice(
  open,
  () => props.fueling?.vehicle.id ?? props.vehicleId,
)

const day = ref('')
const time = ref('')
const kmValue = ref<number | null>(null)
const fuel = ref<FuelType>('gasoline')
const litersValue = ref<number | null>(null)
const total = ref<number | null>(null)
const fullTank = ref(true)

function reset() {
  clear()
  const source = props.fueling
  const when = source ? isoToZoned(source.fueled_at) : nowFields()
  day.value = when.day
  time.value = when.time
  kmValue.value = source?.km ?? selected.value?.current_km ?? null
  fuel.value = (source?.fuel_type ?? selected.value?.fuel_type ?? 'gasoline') as FuelType
  litersValue.value = source ? source.volume_ml / 1000 : null
  total.value = source?.total_cents ?? null
  fullTank.value = source?.full_tank ?? true
}
watch(open, (value) => value && reset(), { immediate: true })
watch(selectedId, () => {
  if (!props.fueling && selected.value) {
    kmValue.value = selected.value.current_km
    fuel.value = (selected.value.fuel_type ?? fuel.value) as FuelType
  }
})

const fuelOptions = computed(() =>
  FUEL_TYPES.map((value) => ({ value, label: t(`garage.fuelShort.${value}`) })),
)
const lastHint = computed(() =>
  selected.value
    ? t('garage.form.lastReading', {
        km: km(selected.value.current_km),
        when: relativeDateTime(selected.value.current_km_at).toLocaleLowerCase(),
      })
    : undefined,
)
/** Convenience preview while typing; the saved value comes from the API (G7). */
const pricePreview = computed(() =>
  total.value && litersValue.value
    ? decimal(total.value / 100 / litersValue.value, 2)
    : decimal(0, 2),
)

async function submit() {
  if (!selected.value || kmValue.value === null || !litersValue.value || !total.value) return
  try {
    await save.mutateAsync({
      vehicleId: selected.value.id,
      id: props.fueling?.id,
      body: {
        fueled_at: zonedToIso(day.value, time.value),
        km: kmValue.value,
        fuel_type: fuel.value,
        volume_ml: Math.round(litersValue.value * 1000),
        total_cents: total.value,
        full_tank: fullTank.value,
      },
    })
    toast.show({ title: t('garage.form.fuelingSaved') })
    open.value = false
  } catch (error) {
    capture(error)
  }
}

const moneyLabel = computed(() => moneyParts(0).symbol)
</script>

<template>
  <PDialog v-model:open="open" :title="t('garage.form.fueling')" icon="fuel" tone="garage">
    <form id="fueling-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="vehicles.length === 0" tone="secondary">{{ t('garage.form.noVehicles') }}</PText>
      <VehiclePicker v-if="!vehicleId && !fueling" v-model="selectedId" :vehicles="vehicles" />
      <PAlert v-if="failure" :title="failure" />
      <div class="form__row">
        <PField :label="t('garage.form.date')" :error="errors.fueled_at">
          <PDateInput v-model="day" />
        </PField>
        <PField :label="t('garage.form.time')">
          <PDateInput v-model="time" type="time" />
        </PField>
        <PField :label="t('garage.form.km')" :hint="lastHint" :error="errors.km">
          <PNumberInput v-model="kmValue" suffix="km" />
        </PField>
      </div>
      <PField :label="t('garage.form.fuelType')" label-as="span" :error="errors.fuel_type">
        <PSegmented v-model="fuel" :options="fuelOptions" :label="t('garage.form.fuelType')" />
      </PField>
      <div class="form__row">
        <PField :label="t('garage.form.liters')" :error="errors.volume_ml">
          <PNumberInput v-model="litersValue" :decimals="2" suffix="L" />
        </PField>
        <PField :label="t('garage.form.totalPaid')" :error="errors.total_cents">
          <PMoneyInput v-model="total" />
        </PField>
        <PField :label="t('garage.form.pricePerLiter')" :hint="t('garage.form.calculated')">
          <PInput
            :model-value="pricePreview"
            :prefix="moneyLabel"
            align="end"
            calculated
            readonly
          />
        </PField>
      </div>
      <PPanel class="form__switch">
        <div class="form__switch-text">
          <PText variant="h3" as="span">{{ t('garage.form.fullTank') }}</PText>
          <PText variant="sm" tone="muted" as="span">{{
            fullTank ? t('garage.form.fullTankHint') : t('garage.form.partialHint')
          }}</PText>
        </div>
        <PSwitch v-model="fullTank" :label="t('garage.form.fullTank')" />
      </PPanel>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="fueling-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!selected"
        >{{ t('garage.form.saveFueling') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
