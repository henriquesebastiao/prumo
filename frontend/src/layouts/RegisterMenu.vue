<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { PCommand, PKbd } from '@/ui'

import type { QuickActionSection } from './nav'

defineProps<{ sections: QuickActionSection[] }>()
const emit = defineEmits<{ select: [id: string] }>()
const { t } = useI18n()
const OPEN_KEY = 'N'
</script>

<template>
  <PCommand
    :groups="sections"
    :placeholder="t('quickActions.search')"
    :empty-label="t('quickActions.empty')"
    @select="emit('select', $event)"
  >
    <template #footer>
      <i18n-t keypath="quickActions.hint" tag="span">
        <template #key
          ><PKbd>{{ OPEN_KEY }}</PKbd></template
        >
      </i18n-t>
    </template>
  </PCommand>
</template>
