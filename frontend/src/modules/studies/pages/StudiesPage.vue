<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute } from 'vue-router'

import { PButton, PPageHeader, PTabs } from '@/ui'

import SessionDialog from '../forms/SessionDialog.vue'

const { t } = useI18n()
const route = useRoute()
const logging = ref(false)

const current = computed(() => String(route.name ?? 'studies.home'))
const section = computed(() => current.value.replace('studies.', '').replace('home', 'today'))
const tabs = computed(() =>
  (['home', 'week', 'subjects', 'plan'] as const).map((name) => ({
    value: `studies.${name}`,
    label: t(`studies.tabs.${name === 'home' ? 'today' : name}`),
    to: { name: `studies.${name}` },
  })),
)
</script>

<template>
  <PPageHeader :overline="t('studies.nav')" :title="t(`studies.titles.${section}`)">
    <PButton variant="primary" icon="add" @click="logging = true">{{
      t('studies.actions.logSession')
    }}</PButton>
  </PPageHeader>
  <PTabs mode="nav" :items="tabs" :model-value="current" :label="t('studies.tabs.label')" />
  <RouterView />
  <SessionDialog v-model:open="logging" />
</template>
