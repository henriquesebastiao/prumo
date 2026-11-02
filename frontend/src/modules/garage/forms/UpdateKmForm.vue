<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { km, relativeDateTime } from '@/lib/format'
import { PAlert, PButton, PField, PNumberInput, useToast } from '@/ui'

import { useAddReading, type Vehicle } from '../api'
import { useFormErrors } from './useGarageForm'

const props = defineProps<{ vehicle: Vehicle; formId: string; showActions?: boolean }>()
const emit = defineEmits<{ done: []; cancel: [] }>()
const { t } = useI18n()
const toast = useToast()
const add = useAddReading()
const { errors, failure, capture, clear } = useFormErrors()
const value = ref<number | null>(props.vehicle.current_km)

watch(
  () => props.vehicle.id,
  () => {
    value.value = props.vehicle.current_km
    clear()
  },
)

const hint = computed(() =>
  t('garage.form.lastReading', {
    km: km(props.vehicle.current_km),
    when: relativeDateTime(props.vehicle.current_km_at).toLocaleLowerCase(),
  }),
)

async function submit() {
  if (value.value === null) return
  try {
    await add.mutateAsync({ vehicleId: props.vehicle.id, km: value.value })
    toast.show({ title: t('garage.form.kmSaved') })
    emit('done')
  } catch (error) {
    capture(error)
  }
}

defineExpose({ pending: add.isPending })
</script>

<template>
  <form :id="formId" class="km-form" novalidate @submit.prevent="submit">
    <PAlert v-if="failure" :title="failure" />
    <PField :label="t('garage.form.km')" :hint="hint" :error="errors.km">
      <PNumberInput v-model="value" suffix="km" />
    </PField>
    <div v-if="showActions" class="km-form__actions">
      <PButton @click="emit('cancel')">{{ t('ui.cancel') }}</PButton>
      <PButton type="submit" variant="primary" :loading="add.isPending.value">{{
        t('ui.save')
      }}</PButton>
    </div>
  </form>
</template>

<style scoped>
.km-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.km-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
