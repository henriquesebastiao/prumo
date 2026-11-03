<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { PButton, PCard, PText } from '@/ui'

const { t } = useI18n()
</script>

<template>
  <PCard as="section">
    <template #header>
      <div class="data__heading">
        <PText as="h2" variant="h2">{{ t('settings.data.title') }}</PText>
        <PText variant="sm" tone="muted">{{ t('settings.data.description') }}</PText>
      </div>
    </template>
    <div class="data__actions">
      <PButton icon="download" href="/api/v1/me/export" download>{{
        t('settings.data.export')
      }}</PButton>
    </div>
  </PCard>
</template>

<style scoped>
.data__heading {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
}

.data__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
