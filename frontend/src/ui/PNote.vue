<script setup lang="ts">
import type { IconName } from './icons'
import PIcon from './PIcon.vue'

withDefaults(defineProps<{ icon?: IconName }>(), { icon: 'info' })
</script>

<template>
  <p class="p-note">
    <PIcon :name="icon" size="sm" />
    <span><slot /></span>
  </p>
</template>

<style scoped>
.p-note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2-5);
  padding: var(--space-3) var(--space-3-5);
  border-radius: var(--radius-note);
  background: var(--color-surface-tint);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

.p-note :deep(.p-icon) {
  margin-top: 1px;
}
</style>
