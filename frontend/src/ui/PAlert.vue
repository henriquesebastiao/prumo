<script setup lang="ts">
import type { IconName } from './icons'
import PIcon from './PIcon.vue'

withDefaults(defineProps<{ title: string; description?: string; icon?: IconName }>(), {
  description: undefined,
  icon: 'alert',
})
</script>

<template>
  <div class="p-alert" role="alert">
    <PIcon :name="icon" />
    <div class="p-alert__body">
      <p class="p-alert__title">{{ title }}</p>
      <p v-if="description || $slots.default" class="p-alert__description">
        <slot>{{ description }}</slot>
      </p>
    </div>
  </div>
</template>

<style scoped>
.p-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3-5) var(--space-4);
  border-radius: var(--radius-alert);
  background: var(--color-danger-container);
  color: var(--color-on-danger-container);
}

.p-alert__body {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-0-5);
}

.p-alert__title {
  font-weight: var(--weight-bold);
}

.p-alert__description {
  font-size: var(--text-sm);
}
</style>
