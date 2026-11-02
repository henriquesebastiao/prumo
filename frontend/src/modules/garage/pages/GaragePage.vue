<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute } from 'vue-router'

import { PButton, PPageHeader, PTabs } from '@/ui'

import VehicleDialog from '../forms/VehicleDialog.vue'

const { t } = useI18n()
const route = useRoute()
const creating = ref(false)

const tabs = computed(() => [
  { value: 'garage.home', label: t('garage.tabs.vehicles'), to: { name: 'garage.home' } },
  { value: 'garage.fuelings', label: t('garage.tabs.fuelings'), to: { name: 'garage.fuelings' } },
  {
    value: 'garage.maintenances',
    label: t('garage.tabs.maintenances'),
    to: { name: 'garage.maintenances' },
  },
  {
    value: 'garage.oil-changes',
    label: t('garage.tabs.oilChanges'),
    to: { name: 'garage.oil-changes' },
  },
  {
    value: 'garage.workshops',
    label: t('garage.tabs.workshops'),
    to: { name: 'garage.workshops' },
  },
])
const current = computed(() => String(route.name ?? 'garage.home'))
</script>

<template>
  <PPageHeader :overline="t('garage.nav')" :title="t('garage.title')">
    <PButton variant="primary" icon="add" @click="creating = true">{{
      t('garage.actions.newVehicle')
    }}</PButton>
  </PPageHeader>
  <PTabs mode="nav" :items="tabs" :model-value="current" :label="t('garage.tabs.label')" />
  <RouterView />
  <VehicleDialog v-model:open="creating" />
</template>
