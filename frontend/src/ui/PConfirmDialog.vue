<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { IconName } from './icons'
import PButton from './PButton.vue'
import PDialog from './PDialog.vue'

withDefaults(
  defineProps<{
    title: string
    description: string
    confirmLabel: string
    cancelLabel?: string
    tone?: 'danger' | 'accent'
    icon?: IconName
    loading?: boolean
    inline?: boolean
  }>(),
  { cancelLabel: undefined, tone: 'danger', icon: 'trash' },
)

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ confirm: [] }>()
const { t } = useI18n()
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="title"
    :description="description"
    size="s"
    :icon="icon"
    :tone="tone"
    :inline="inline"
  >
    <template #footer>
      <PButton @click="open = false">{{ cancelLabel ?? t('ui.cancel') }}</PButton>
      <PButton
        :variant="tone === 'danger' ? 'danger' : 'primary'"
        :loading="loading"
        @click="emit('confirm')"
        >{{ confirmLabel }}</PButton
      >
    </template>
  </PDialog>
</template>
