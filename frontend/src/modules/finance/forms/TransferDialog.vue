<script setup lang="ts">
/** Quick action: the transaction dialog on the Transfer tab. */
import TransactionDialog from './TransactionDialog.vue'

const open = defineModel<boolean>('open', { default: false })
</script>

<template>
  <TransactionDialog v-model:open="open" kind="transfer" />
</template>
