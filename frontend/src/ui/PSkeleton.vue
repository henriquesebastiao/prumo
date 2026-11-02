<script setup lang="ts">
withDefaults(
  defineProps<{ width?: string; height?: string; shape?: 'line' | 'tile' | 'circle' }>(),
  { width: '100%', height: '12px', shape: 'line' },
)
</script>

<template>
  <span
    class="p-skeleton"
    :class="`p-skeleton--${shape}`"
    :style="{ width, height }"
    aria-hidden="true"
  />
</template>

<style scoped>
.p-skeleton {
  display: block;
  flex: none;
  border-radius: var(--radius-sm);
  background: var(--color-fill);
  animation: p-pulse var(--duration-pulse) ease-in-out infinite;
}

.p-skeleton--tile {
  border-radius: var(--radius-tile);
}

.p-skeleton--circle {
  border-radius: 50%;
}
</style>
