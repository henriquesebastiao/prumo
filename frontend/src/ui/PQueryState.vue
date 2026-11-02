<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'

import PAlert from './PAlert.vue'
import PButton from './PButton.vue'
import PSkeleton from './PSkeleton.vue'
import PSpinner from './PSpinner.vue'

/**
 * Loading, error and empty states of a server query, with the patterns of the design:
 * skeleton + "Carregando dados do servidor…", error alert with retry, or the empty slot.
 */
withDefaults(
  defineProps<{
    loading: boolean
    error?: unknown
    empty?: boolean
    /** Title of the error alert ("Não foi possível carregar as transações"). */
    errorTitle?: string
  }>(),
  { error: undefined, empty: false, errorTitle: undefined },
)
const emit = defineEmits<{ retry: [] }>()
const { t, te } = useI18n()
const showDetails = ref(false)
</script>

<template>
  <div v-if="loading" class="p-query-state" aria-busy="true">
    <slot name="loading">
      <div class="p-query-state__skeleton">
        <PSkeleton shape="tile" width="40px" height="40px" />
        <span class="p-query-state__lines">
          <PSkeleton width="40%" height="14px" />
          <PSkeleton width="24%" height="10px" />
        </span>
      </div>
      <PSkeleton height="12px" />
      <PSkeleton width="70%" height="12px" />
    </slot>
    <p class="p-query-state__loading"><PSpinner />{{ t('ui.loadingServer') }}</p>
  </div>
  <div v-else-if="error" class="p-query-state">
    <PAlert
      :title="errorTitle ?? t('ui.loadFailed')"
      :description="errorMessage(error, { t, te })"
    />
    <div class="p-query-state__actions">
      <PButton variant="primary" icon="refresh" @click="emit('retry')">{{ t('ui.retry') }}</PButton>
      <PButton variant="ghost" @click="showDetails = !showDetails">{{ t('ui.details') }}</PButton>
    </div>
    <code v-if="showDetails" class="p-query-state__details">{{
      (error as { code?: string }).code
    }}</code>
  </div>
  <slot v-else-if="empty" name="empty" />
  <slot v-else />
</template>

<style scoped>
.p-query-state {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.p-query-state__skeleton {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.p-query-state__lines {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--space-2);
}

.p-query-state__loading {
  display: flex;
  align-items: center;
  gap: var(--space-2-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.p-query-state__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.p-query-state__details {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}
</style>
