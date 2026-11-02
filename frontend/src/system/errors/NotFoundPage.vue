<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { PButton, PEmptyState } from '@/ui'

const { t } = useI18n()
</script>

<template>
  <PEmptyState
    variant="card"
    icon="search"
    :title="t('notFound.title')"
    :description="t('notFound.description')"
  >
    <PButton variant="primary" :to="{ name: 'home' }">{{ t('notFound.action') }}</PButton>
  </PEmptyState>
</template>
