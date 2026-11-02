<script setup lang="ts">
withDefaults(defineProps<{ disabled?: boolean; id?: string }>(), { id: undefined })
const model = defineModel<boolean>({ default: false })
</script>

<template>
  <label class="p-checkbox">
    <input :id="id" v-model="model" type="checkbox" :disabled="disabled" />
    <span><slot /></span>
  </label>
</template>

<style scoped>
.p-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2-5);
  font-size: var(--text-md);
  cursor: pointer;
}

.p-checkbox input {
  width: 20px;
  height: 20px;
  margin: 0;
  accent-color: var(--color-accent);
  cursor: pointer;
}
</style>
