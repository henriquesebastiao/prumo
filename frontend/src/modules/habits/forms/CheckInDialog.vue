<script setup lang="ts">
/** "Marcar hábitos" (quick action, shortcut H): today's habits, to tap or count. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { PButton, PDialog, PEmptyState, PQueryState } from '@/ui'

import { useToday } from '../api'
import TodayList from '../components/TodayList.vue'

const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const query = useToday()
const today = computed(() => query.data.value)
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('habits.form.titles.checkIn')"
    icon="list-checks"
    tone="habits"
  >
    <PQueryState
      :loading="query.isPending.value"
      :error="query.error.value"
      :error-title="t('ui.loadFailed')"
    >
      <TodayList v-if="today?.items.length" :items="today.items" :today="today.today" />
      <PEmptyState
        v-else
        :title="t('habits.today.empty')"
        :description="t('habits.today.emptyHint')"
        icon="list-checks"
        tone="habits"
      />
    </PQueryState>
    <template #footer>
      <PButton variant="primary" @click="open = false">{{ t('ui.close') }}</PButton>
    </template>
  </PDialog>
</template>
