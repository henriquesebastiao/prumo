<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

import PButton from './PButton.vue'

withDefaults(
  defineProps<{
    title: string
    overline?: string
    back?: { label: string; to: RouteLocationRaw }
    size?: 'md' | 'sm'
  }>(),
  { overline: undefined, back: undefined, size: 'md' },
)
</script>

<template>
  <header class="p-page-header" :class="`p-page-header--${size}`">
    <div class="p-page-header__titles">
      <PButton v-if="back" :to="back.to" icon="chevron-left" class="p-page-header__back">{{
        back.label
      }}</PButton>
      <p v-if="overline" class="p-page-header__overline">{{ overline }}</p>
      <h1 class="p-page-header__title">{{ title }}</h1>
    </div>
    <div v-if="$slots.default" class="p-page-header__actions"><slot /></div>
  </header>
</template>

<style scoped>
.p-page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-3) var(--space-4);
}

.p-page-header__titles {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: flex-start;
}

.p-page-header__back {
  margin-bottom: var(--space-3);
  padding-left: var(--space-2-5);
}

.p-page-header__overline {
  color: var(--color-text-muted);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
}

.p-page-header__title {
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.p-page-header--sm .p-page-header__overline {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
}

.p-page-header--sm .p-page-header__title {
  font-size: var(--text-2xl-plus);
  line-height: 1.2;
}

.p-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}
</style>
