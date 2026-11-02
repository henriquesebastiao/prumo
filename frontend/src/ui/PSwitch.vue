<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from 'reka-ui'

withDefaults(defineProps<{ label?: string; disabled?: boolean; id?: string }>(), {
  label: undefined,
  id: undefined,
})
const model = defineModel<boolean>({ default: false })
</script>

<template>
  <SwitchRoot :id="id" v-model="model" class="p-switch" :aria-label="label" :disabled="disabled">
    <SwitchThumb class="p-switch__thumb" />
  </SwitchRoot>
</template>

<style scoped>
.p-switch {
  position: relative;
  flex: none;
  width: 52px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
  transition: background-color var(--duration-base) var(--easing-standard);
}

.p-switch[data-state='checked'] {
  background: var(--color-accent);
}

.p-switch:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.p-switch__thumb {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-knob);
  transition: transform var(--duration-base) var(--easing-standard);
}

.p-switch[data-state='checked'] .p-switch__thumb {
  background: var(--color-accent-contrast);
  transform: translateX(20px);
}
</style>
