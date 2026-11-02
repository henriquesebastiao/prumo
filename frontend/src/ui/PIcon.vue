<script setup lang="ts">
import { computed } from 'vue'

import { icons, type IconName } from './icons'

const props = withDefaults(
  defineProps<{
    name: IconName
    size?: 'sm' | 'md' | 'lg' | 'xl'
    /** Accessible name. Without it the icon is decorative (`aria-hidden`). */
    label?: string
  }>(),
  { size: 'md', label: undefined },
)

const component = computed(() => icons[props.name])
const strokeWidth = computed(() => (props.size === 'xl' ? 1.8 : 2))
</script>

<template>
  <component
    :is="component"
    class="p-icon"
    :class="`p-icon--${size}`"
    :stroke-width="strokeWidth"
    :aria-hidden="label ? undefined : 'true'"
    :aria-label="label"
    :role="label ? 'img' : undefined"
    focusable="false"
  />
</template>

<style scoped>
.p-icon {
  flex: none;
  width: var(--icon-md);
  height: var(--icon-md);
}

.p-icon--sm {
  width: var(--icon-sm);
  height: var(--icon-sm);
}

.p-icon--lg {
  width: var(--icon-lg);
  height: var(--icon-lg);
}

.p-icon--xl {
  width: var(--icon-xl);
  height: var(--icon-xl);
}

.p-icon[data-tone] {
  color: var(--tone);
}
</style>
