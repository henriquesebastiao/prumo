<script setup lang="ts">
import { PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'

withDefaults(
  defineProps<{
    side?: 'top' | 'right' | 'bottom' | 'left'
    align?: 'start' | 'center' | 'end'
    label?: string
    portal?: boolean
    width?: string
  }>(),
  { side: 'bottom', align: 'start', label: undefined, portal: true, width: '340px' },
)
const open = defineModel<boolean>('open', { default: false })
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child><slot name="trigger" /></PopoverTrigger>
    <PopoverPortal :disabled="!portal">
      <PopoverContent
        class="p-popover"
        :side="side"
        :align="align"
        :side-offset="8"
        :collision-padding="16"
        :aria-label="label"
        :style="{ width }"
      >
        <slot />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style scoped>
.p-popover {
  z-index: 50;
  display: flex;
  max-width: calc(100vw - 32px);
  flex-direction: column;
  gap: var(--space-3-5);
  padding: var(--space-4-5);
  border-radius: var(--radius-menu);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-lg);
}
</style>
