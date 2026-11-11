<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute } from 'vue-router'

import { PButton, PPageHeader, PTabs } from '@/ui'

import HabitDialog from '../forms/HabitDialog.vue'

const { t } = useI18n()
const route = useRoute()
const creating = ref(false)

const current = computed(() => String(route.name ?? 'habits.home'))
const section = computed(() => (current.value === 'habits.list' ? 'list' : 'today'))
const tabs = computed(() => [
  { value: 'habits.home', label: t('habits.tabs.today'), to: { name: 'habits.home' } },
  { value: 'habits.list', label: t('habits.tabs.list'), to: { name: 'habits.list' } },
])
</script>

<template>
  <PPageHeader :overline="t('habits.nav')" :title="t(`habits.titles.${section}`)">
    <PButton variant="primary" icon="add" @click="creating = true">{{
      t('habits.actions.newHabit')
    }}</PButton>
  </PPageHeader>
  <PTabs mode="nav" :items="tabs" :model-value="current" :label="t('habits.tabs.label')" />
  <RouterView />
  <HabitDialog v-model:open="creating" />
</template>
