<script setup lang="ts">
import { computed, useAttrs } from 'vue'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'

defineOptions({ inheritAttrs: false })

/** Layout attributes (class, style) go to the wrapper; aria and events go to the button. */
const attrs = useAttrs()
const rootAttrs = computed(() => ({ class: attrs.class, style: attrs.style }))
const buttonAttrs = computed(() =>
  Object.fromEntries(Object.entries(attrs).filter(([key]) => key !== 'class' && key !== 'style')),
)

withDefaults(
  defineProps<{
    icon: IconName
    label: string
    /** `rail`: square button with the label below. `floating`: phone button over the content. */
    variant?: 'rail' | 'floating'
  }>(),
  { variant: 'rail' },
)
</script>

<template>
  <div class="p-fab" :class="`p-fab--${variant}`" v-bind="rootAttrs">
    <button
      type="button"
      class="p-fab__button"
      :aria-label="variant === 'floating' ? label : undefined"
      v-bind="buttonAttrs"
    >
      <PIcon :name="icon" />
    </button>
    <span v-if="variant === 'rail'" class="p-fab__label" aria-hidden="true">{{ label }}</span>
  </div>
</template>

<style scoped>
.p-fab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.p-fab__button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height-lg);
  height: var(--control-height-lg);
  border: 0;
  border-radius: var(--radius-fab);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.p-fab--floating .p-fab__button {
  width: 56px;
  height: 56px;
  box-shadow: var(--shadow-lg);
}
</style>
