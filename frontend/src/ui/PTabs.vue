<script setup lang="ts" generic="V extends string">
import { TabsList, TabsRoot, TabsTrigger } from 'reka-ui'
import { RouterLink } from 'vue-router'

import type { TabItem } from './types'

withDefaults(
  defineProps<{
    items: TabItem<V>[]
    label: string
    /** `nav`: links between pages (aria-current). `tabs`: a tablist with <PTabPanel> panels. */
    mode?: 'tabs' | 'nav'
  }>(),
  { mode: 'tabs' },
)
const model = defineModel<V>()
</script>

<template>
  <nav v-if="mode === 'nav'" class="p-tabs" :aria-label="label">
    <RouterLink
      v-for="item in items"
      :key="item.value"
      :to="item.to ?? ''"
      class="p-tabs__tab"
      :aria-current="model === item.value ? 'page' : undefined"
    >
      {{ item.label
      }}<span v-if="item.count !== undefined" class="p-tabs__count">{{ item.count }}</span>
    </RouterLink>
  </nav>
  <TabsRoot v-else v-model="model" class="p-tabs__root" activation-mode="automatic">
    <div class="p-tabs__bar">
      <slot name="start" />
      <TabsList class="p-tabs" :aria-label="label">
        <TabsTrigger
          v-for="item in items"
          :key="item.value"
          :value="item.value"
          class="p-tabs__tab"
        >
          {{ item.label
          }}<span v-if="item.count !== undefined" class="p-tabs__count">{{ item.count }}</span>
        </TabsTrigger>
      </TabsList>
      <span v-if="$slots.end" class="p-tabs__spacer" />
      <slot name="end" />
    </div>
    <slot />
  </TabsRoot>
</template>

<style scoped>
.p-tabs__root {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.p-tabs__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-4);
}

.p-tabs__spacer {
  flex: 1;
}

/* One row that scrolls sideways on narrow screens (five sections do not fit a phone). */
.p-tabs {
  display: flex;
  min-width: 0;
  max-width: 100%;
  gap: var(--space-1-5);
  overflow-x: auto;
  scrollbar-width: none;
}

.p-tabs::-webkit-scrollbar {
  display: none;
}

.p-tabs__tab {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: var(--space-1-5);
  height: var(--tab-height);
  padding: 0 var(--space-3-5);
  border: 0;
  border-radius: var(--radius-full);
  background: var(--color-surface-tint);
  color: var(--color-text-secondary);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  text-decoration: none;
}

.p-tabs__tab[data-state='active'],
.p-tabs__tab[aria-current='page'] {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  font-weight: var(--weight-bold);
}

.p-tabs__count {
  font-weight: var(--weight-semibold);
  opacity: 0.7;
}
</style>
