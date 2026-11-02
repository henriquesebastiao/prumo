<script setup lang="ts">
import { TabsContent } from 'reka-ui'

defineProps<{ value: string }>()
</script>

<template>
  <TabsContent :value="value" class="p-tab-panel"><slot /></TabsContent>
</template>

<style scoped>
.p-tab-panel:focus-visible {
  outline-offset: 4px;
}
</style>
