<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { PButton, PDialog, PText } from '@/ui'

import VehiclePicker from '../components/VehiclePicker.vue'
import UpdateKmForm from './UpdateKmForm.vue'
import { useVehicleChoice } from './useGarageForm'

const props = defineProps<{ vehicleId?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const { vehicles, selectedId, selected } = useVehicleChoice(open, () => props.vehicleId)
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('garage.form.updateKm')"
    icon="gauge"
    tone="garage"
    size="s"
  >
    <div class="km-dialog">
      <PText v-if="vehicles.length === 0" tone="secondary">{{ t('garage.form.noVehicles') }}</PText>
      <VehiclePicker v-if="!vehicleId" v-model="selectedId" :vehicles="vehicles" />
      <UpdateKmForm
        v-if="selected"
        :vehicle="selected"
        form-id="update-km-form"
        @done="open = false"
      />
    </div>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton type="submit" form="update-km-form" variant="primary" :disabled="!selected">{{
        t('ui.save')
      }}</PButton>
    </template>
  </PDialog>
</template>

<style scoped>
.km-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
</style>
