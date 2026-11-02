<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; size?: 'md' | 'lg' }>(), {
  size: 'md',
})

const initials = computed(() => {
  const words = props.name.trim().split(/\s+/).filter(Boolean)
  const first = words[0]?.[0] ?? ''
  const last = words.length > 1 ? (words.at(-1)?.[0] ?? '') : ''
  return (first + last).toLocaleUpperCase()
})
</script>

<template>
  <span class="p-avatar" :class="`p-avatar--${size}`" role="img" :aria-label="name">{{
    initials
  }}</span>
</template>

<style scoped>
.p-avatar {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-avatar);
  background: var(--color-border);
  color: var(--color-text);
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
}

.p-avatar--lg {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-avatar-lg);
  font-size: var(--text-2xl);
}
</style>
