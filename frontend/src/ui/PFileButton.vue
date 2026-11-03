<script setup lang="ts">
/** A button that opens the file chooser and emits the chosen file. */
import { ref } from 'vue'

import type { IconName } from './icons'
import PButton from './PButton.vue'

withDefaults(defineProps<{ accept?: string; icon?: IconName; block?: boolean }>(), {
  accept: undefined,
  icon: 'image',
})
const emit = defineEmits<{ select: [file: File] }>()
const input = ref<HTMLInputElement>()

function onChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) emit('select', file)
  target.value = ''
}
</script>

<template>
  <PButton :icon="icon" :block="block" @click="input?.click()"><slot /></PButton>
  <input
    ref="input"
    type="file"
    class="p-sr-only"
    tabindex="-1"
    aria-hidden="true"
    :accept="accept"
    @change="onChange"
  />
</template>
