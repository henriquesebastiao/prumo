<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from 'vue-router'

import PIcon from './PIcon.vue'

withDefaults(defineProps<{ to?: RouteLocationRaw; href?: string; chevron?: boolean }>(), {
  to: undefined,
  href: undefined,
  chevron: true,
})
</script>

<template>
  <component :is="to ? RouterLink : 'a'" :to="to" :href="href" class="p-link">
    <slot />
    <PIcon v-if="chevron" name="chevron-right" size="sm" />
  </component>
</template>

<style scoped>
.p-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-0-5);
  min-height: var(--control-height);
  padding: 0 var(--space-1) 0 var(--space-2-5);
  color: var(--color-text-secondary);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  text-decoration: none;
  white-space: nowrap;
}

.p-link:hover {
  color: var(--color-text);
}
</style>
