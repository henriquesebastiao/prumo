<script setup lang="ts">
import { PCard } from '@/ui'

defineProps<{ title: string; note?: string }>()
</script>

<template>
  <PCard as="section" :title="title">
    <slot />
    <p v-if="note" class="showcase-note">{{ note }}</p>
  </PCard>
</template>

<style scoped>
.showcase-note {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}
</style>
