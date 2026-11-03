<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from 'vue-router'

withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    to?: RouteLocationRaw
    /** Highlights the item being edited in a side panel. */
    current?: boolean
  }>(),
  { title: undefined, subtitle: undefined, to: undefined },
)
</script>

<template>
  <li class="p-list-item" :class="{ 'p-list-item--current': current }">
    <component :is="to ? RouterLink : 'div'" :to="to" class="p-list-item__row">
      <slot name="leading" />
      <span class="p-list-item__body">
        <slot>
          <span class="p-list-item__title">{{ title }}</span>
          <span v-if="subtitle || $slots.subtitle" class="p-list-item__subtitle"
            ><slot name="subtitle">{{ subtitle }}</slot></span
          >
        </slot>
      </span>
      <span v-if="$slots.trailing" class="p-list-item__trailing"><slot name="trailing" /></span>
    </component>
  </li>
</template>

<style scoped>
.p-list-item {
  border-top: 1px solid var(--color-divider);
}

.p-list-item:first-child {
  border-top: 0;
}

.p-list-item--current,
.p-list-item--current + .p-list-item {
  border-top-color: transparent;
}

.p-list-item--current {
  margin: 0 calc(-1 * var(--space-3));
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-inset);
}

/* On narrow screens the trailing content moves to its own line, aligned to the end. */
.p-list-item__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2-5) 0;
  color: inherit;
  text-decoration: none;
}

.p-list-item__body {
  display: flex;
  min-width: 0;
  flex: 1 1 10rem;
  flex-direction: column;
}

.p-list-item__trailing {
  display: flex;
  flex: none;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

.p-list-item__title {
  font-weight: var(--weight-bold);
}

.p-list-item__subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
