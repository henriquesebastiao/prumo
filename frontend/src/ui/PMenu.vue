<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'reka-ui'
import { useRouter } from 'vue-router'

import PIcon from './PIcon.vue'
import PKbd from './PKbd.vue'
import type { MenuEntry } from './types'

withDefaults(
  defineProps<{
    items: MenuEntry[]
    side?: 'top' | 'right' | 'bottom' | 'left'
    align?: 'start' | 'center' | 'end'
    portal?: boolean
  }>(),
  { side: 'bottom', align: 'end', portal: true },
)
const open = defineModel<boolean>('open', { default: false })
const router = useRouter()

function select(entry: MenuEntry) {
  if (entry.type === 'separator' || entry.type === 'label') return
  if (entry.to) void router.push(entry.to)
  entry.onSelect?.()
}
</script>

<template>
  <DropdownMenuRoot v-model:open="open">
    <DropdownMenuTrigger as-child><slot name="trigger" /></DropdownMenuTrigger>
    <DropdownMenuPortal :disabled="!portal">
      <DropdownMenuContent
        class="p-menu"
        :side="side"
        :align="align"
        :side-offset="8"
        :collision-padding="16"
      >
        <slot name="header" />
        <template v-for="(entry, index) in items" :key="index">
          <DropdownMenuSeparator v-if="entry.type === 'separator'" class="p-menu__separator" />
          <DropdownMenuLabel v-else-if="entry.type === 'label'" class="p-menu__label">{{
            entry.label
          }}</DropdownMenuLabel>
          <DropdownMenuItem
            v-else
            class="p-menu__item"
            :class="{ 'p-menu__item--danger': entry.danger }"
            @select="select(entry)"
          >
            <PIcon v-if="entry.icon" :name="entry.icon" :data-tone="entry.tone" />
            {{ entry.label }}
            <PKbd v-if="entry.shortcut" class="p-menu__shortcut">{{ entry.shortcut }}</PKbd>
            <PIcon v-else-if="entry.checked" name="check" size="sm" class="p-menu__shortcut" />
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<style src="./menu.css"></style>
