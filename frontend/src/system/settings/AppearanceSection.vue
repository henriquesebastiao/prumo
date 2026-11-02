<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useThemeStore } from '@/app/stores/theme'
import type { ThemePreference } from '@/design/theme'
import { useUpdatePreferences } from '@/system/api'
import { PCard, PChoiceCards, PText, PThemePreview } from '@/ui'

const { t } = useI18n()
const theme = useThemeStore()
const update = useUpdatePreferences()

const options = computed(() => [
  { value: 'light' as const, label: t('theme.light') },
  { value: 'dark' as const, label: t('theme.dark') },
  { value: 'system' as const, label: t('theme.system'), description: t('theme.systemHint') },
])

const selected = computed({
  get: () => theme.preference,
  set: (value: ThemePreference) => {
    theme.set(value)
    update.mutate({ theme: value })
  },
})
</script>

<template>
  <PCard as="section">
    <template #header>
      <div class="appearance__heading">
        <PText as="h2" variant="h2">{{ t('settings.appearance.title') }}</PText>
        <PText variant="sm" tone="muted">{{ t('settings.appearance.description') }}</PText>
      </div>
    </template>
    <PChoiceCards v-model="selected" :options="options" :label="t('theme.label')">
      <template #preview="{ option }">
        <PThemePreview :theme="option.value" />
      </template>
    </PChoiceCards>
  </PCard>
</template>

<style scoped>
.appearance__heading {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
}
</style>
