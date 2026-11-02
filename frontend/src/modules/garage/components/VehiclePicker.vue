<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { PSegmented } from '@/ui'

import type { Vehicle } from '../api'

const props = defineProps<{ vehicles: Vehicle[] }>()
const model = defineModel<string>({ required: true })
const { t } = useI18n()
const options = computed(() => props.vehicles.map((v) => ({ value: v.id, label: v.name })))
</script>

<template>
  <PSegmented
    v-if="vehicles.length > 1"
    v-model="model"
    :options="options"
    :label="t('garage.form.vehicleLabel')"
    block
  />
</template>
