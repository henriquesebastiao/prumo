<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import {
  PAlert,
  PButton,
  PConfirmDialog,
  PDialog,
  PField,
  PInput,
  PNumberInput,
  PPanel,
  PSegmented,
  PSelect,
  PSwitch,
  PText,
  PTextarea,
  useToast,
} from '@/ui'

import { useDeleteVehicle, useSaveVehicle, type Vehicle } from '../api'
import { FUEL_TYPES } from '../helpers'
import { useFormErrors } from './useGarageForm'

const props = defineProps<{ vehicle?: Vehicle }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [vehicle: Vehicle] }>()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const save = useSaveVehicle()
const remove = useDeleteVehicle()
const { errors, failure, capture, clear } = useFormErrors()

const kind = ref<'car' | 'motorcycle'>('car')
const name = ref('')
const brand = ref('')
const model = ref('')
const year = ref<number | null>(null)
const currentKm = ref<number | null>(null)
const fuel = ref<string>('none')
const byKm = ref(true)
const intervalKm = ref<number | null>(10000)
const byTime = ref(true)
const intervalMonths = ref<number | null>(12)
const notes = ref('')
const confirmDelete = ref(false)

function reset() {
  clear()
  const v = props.vehicle
  kind.value = v?.kind ?? 'car'
  name.value = v?.name ?? ''
  brand.value = v?.brand ?? ''
  model.value = v?.model ?? ''
  year.value = v?.year ?? new Date().getFullYear()
  currentKm.value = v?.current_km ?? null
  fuel.value = v?.fuel_type ?? 'none'
  byKm.value = v ? v.oil_interval_km !== null : true
  intervalKm.value = v?.oil_interval_km ?? 10000
  byTime.value = v ? v.oil_interval_months !== null : true
  intervalMonths.value = v?.oil_interval_months ?? 12
  notes.value = v?.notes ?? ''
}
watch(open, (value) => value && reset(), { immediate: true })

const kinds = computed(() => [
  { value: 'car' as const, label: t('garage.kind.car'), icon: 'car' as const },
  { value: 'motorcycle' as const, label: t('garage.kind.motorcycle'), icon: 'motorcycle' as const },
])
const fuels = computed(() => [
  { value: 'none', label: t('garage.form.noFuel') },
  ...FUEL_TYPES.map((value) => ({ value, label: t(`garage.fuel.${value}`) })),
])

async function submit() {
  if (currentKm.value === null || year.value === null) return
  const body = {
    kind: kind.value,
    name: name.value,
    brand: brand.value,
    model: model.value,
    year: year.value,
    current_km: currentKm.value,
    fuel_type: fuel.value === 'none' ? null : (fuel.value as (typeof FUEL_TYPES)[number]),
    oil_interval_km: byKm.value ? intervalKm.value : null,
    oil_interval_months: byTime.value ? intervalMonths.value : null,
    notes: notes.value.trim() || null,
  }
  try {
    const saved = await save.mutateAsync({ id: props.vehicle?.id, body })
    toast.show({ title: t('garage.form.saved') })
    open.value = false
    emit('saved', saved)
  } catch (error) {
    capture(error, 'current_km')
  }
}

async function destroy() {
  if (!props.vehicle) return
  await remove.mutateAsync(props.vehicle.id)
  confirmDelete.value = false
  open.value = false
  toast.show({ title: t('garage.form.deleted') })
  await router.push({ name: 'garage.home' })
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t(vehicle ? 'garage.form.editVehicle' : 'garage.form.newVehicle')"
    :description="vehicle?.name"
    icon="car"
    tone="garage"
  >
    <form id="vehicle-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('garage.form.kind')" label-as="span" :error="errors.kind">
        <PSegmented v-model="kind" :options="kinds" :label="t('garage.form.kind')" />
      </PField>
      <PField :label="t('garage.form.name')" :hint="t('garage.form.nameHint')" :error="errors.name">
        <PInput v-model="name" :maxlength="80" />
      </PField>
      <div class="form__row">
        <PField :label="t('garage.form.brand')" :error="errors.brand">
          <PInput v-model="brand" :maxlength="60" />
        </PField>
        <PField :label="t('garage.form.model')" :error="errors.model">
          <PInput v-model="model" :maxlength="60" />
        </PField>
        <PField :label="t('garage.form.year')" :error="errors.year">
          <PNumberInput v-model="year" />
        </PField>
      </div>
      <div class="form__row">
        <PField :label="t('garage.form.currentKm')" :error="errors.current_km">
          <PNumberInput v-model="currentKm" suffix="km" />
        </PField>
        <PField :label="t('garage.form.fuel')" :error="errors.fuel_type">
          <PSelect v-model="fuel" :options="fuels" />
        </PField>
      </div>
      <PPanel class="form__stack">
        <PText variant="h3">{{ t('garage.form.oilTitle') }}</PText>
        <PText variant="sm" tone="muted">{{ t('garage.form.oilHint') }}</PText>
        <div class="form__switch">
          <PText as="span">{{ t('garage.form.byKm') }}</PText>
          <PSwitch v-model="byKm" :label="t('garage.form.byKm')" />
        </div>
        <PField v-if="byKm" :label="t('garage.form.every')" :error="errors.oil_interval_km">
          <PNumberInput v-model="intervalKm" suffix="km" />
        </PField>
        <div class="form__switch">
          <PText as="span">{{ t('garage.form.byTime') }}</PText>
          <PSwitch v-model="byTime" :label="t('garage.form.byTime')" />
        </div>
        <PField v-if="byTime" :label="t('garage.form.every')" :error="errors.oil_interval_months">
          <PNumberInput v-model="intervalMonths" :suffix="t('garage.form.months')" />
        </PField>
      </PPanel>
      <PField :label="t('garage.form.notes')" optional>
        <PTextarea v-model="notes" :rows="3" />
      </PField>
    </form>
    <template #footer>
      <PButton
        v-if="vehicle"
        variant="ghost"
        icon="trash"
        class="form__danger"
        @click="confirmDelete = true"
        >{{ t('garage.actions.delete') }}</PButton
      >
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="vehicle-form"
        variant="primary"
        :loading="save.isPending.value"
        >{{ t(vehicle ? 'garage.form.save' : 'garage.form.create') }}</PButton
      >
    </template>
  </PDialog>
  <PConfirmDialog
    v-if="vehicle"
    v-model:open="confirmDelete"
    :title="t('garage.form.deleteVehicleTitle', { name: vehicle.name })"
    :description="t('garage.form.deleteVehicleDescription')"
    :confirm-label="t('garage.actions.delete')"
    :loading="remove.isPending.value"
    @confirm="destroy"
  />
</template>

<style src="./form.css" scoped></style>
<style scoped>
.form__danger {
  margin-right: auto;
}
</style>
