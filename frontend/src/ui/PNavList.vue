<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from 'vue-router'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'

defineProps<{
  label: string
  items: (
    | { type: 'separator' }
    | {
        type?: 'link' | 'button'
        key: string
        label: string
        icon?: IconName
        to?: RouteLocationRaw
        /** Plain link, for anchors inside the page (`#perfil`). */
        href?: string
        current?: boolean
        danger?: boolean
        onClick?: () => void
      }
  )[]
}>()
</script>

<template>
  <nav class="p-nav-list" :aria-label="label">
    <template v-for="(item, index) in items" :key="item.type === 'separator' ? index : item.key">
      <span v-if="item.type === 'separator'" class="p-nav-list__separator" />
      <component
        :is="item.to ? RouterLink : item.href ? 'a' : 'button'"
        v-else
        :to="item.to"
        :href="item.href"
        :type="item.to || item.href ? undefined : 'button'"
        class="p-nav-list__item"
        :class="{
          'p-nav-list__item--danger': item.danger,
          'p-nav-list__item--current': item.current,
        }"
        :aria-current="item.current ? 'true' : undefined"
        @click="item.onClick?.()"
      >
        <PIcon v-if="item.icon" :name="item.icon" />
        {{ item.label }}
      </component>
    </template>
  </nav>
</template>

<style scoped>
.p-nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
}

.p-nav-list__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 48px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-menu-item);
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  text-align: left;
  text-decoration: none;
}

.p-nav-list__item:hover,
.p-nav-list__item--current {
  background: var(--color-surface-tint);
}

.p-nav-list__item--danger {
  color: var(--color-danger);
}

.p-nav-list__separator {
  height: 1px;
  margin: var(--space-1-5) var(--space-2);
  background: var(--color-divider);
}
</style>
