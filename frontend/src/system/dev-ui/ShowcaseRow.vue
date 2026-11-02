<script setup lang="ts">
defineProps<{ label?: string; stack?: boolean }>()
</script>

<template>
  <div class="showcase-row">
    <span v-if="label" class="showcase-row__label">{{ label }}</span>
    <div class="showcase-row__items" :class="{ 'showcase-row__items--stack': stack }">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.showcase-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.showcase-row__label {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.showcase-row__items {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-3);
}

.showcase-row__items--stack {
  flex-direction: column;
  align-items: stretch;
}
</style>
