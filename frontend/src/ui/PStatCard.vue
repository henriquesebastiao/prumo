<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value?: string
    caption?: string
    variant?: 'default' | 'flat'
    /** Color of the value (for example `success` for a positive result). */
    valueTone?: 'default' | 'success' | 'danger'
  }>(),
  { value: undefined, caption: undefined, variant: 'default', valueTone: 'default' },
)
</script>

<template>
  <div class="p-stat" :class="`p-stat--${variant}`">
    <span class="p-stat__label">{{ label }}</span>
    <span class="p-stat__value" :class="`p-stat__value--${valueTone}`"
      ><slot>{{ value }}</slot></span
    >
    <span v-if="caption || $slots.caption" class="p-stat__caption"
      ><slot name="caption">{{ caption }}</slot></span
    >
  </div>
</template>

<style scoped>
.p-stat {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-0-5);
  padding: var(--space-4) var(--space-4-5);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.p-stat--flat {
  border: 1px solid var(--color-divider);
  box-shadow: none;
}

.p-stat__label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}

.p-stat__value {
  font-size: var(--text-2xl);
  font-weight: var(--weight-heavy);
  line-height: 1.2;
  letter-spacing: var(--tracking-snug);
  white-space: nowrap;
}

.p-stat__value--success {
  color: var(--color-on-success-container);
}

.p-stat__value--danger {
  color: var(--color-danger);
}

.p-stat__caption {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}
</style>
