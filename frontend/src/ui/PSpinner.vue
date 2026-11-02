<script setup lang="ts">
withDefaults(defineProps<{ size?: 'sm' | 'md'; label?: string }>(), {
  size: 'md',
  label: undefined,
})
</script>

<template>
  <span
    class="p-spinner"
    :class="`p-spinner--${size}`"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
  />
</template>

<style scoped>
.p-spinner {
  display: inline-block;
  flex: none;
  width: 20px;
  height: 20px;
  border: 2.5px solid var(--color-fill);
  border-top-color: var(--color-text);
  border-radius: 50%;
  animation: p-spin 0.8s linear infinite;
}

.p-spinner--sm {
  width: 16px;
  height: 16px;
  border-width: 2px;
}
</style>
