import type { RouteLocationRaw } from 'vue-router'

import type { IconName } from '@/ui'

export interface NavItem {
  key: string
  label: string
  icon: IconName
  to: RouteLocationRaw
  /** Module id (color of the indicator); absent for Início and Módulos. */
  tone?: string
  current: boolean
}

export interface QuickActionItem {
  id: string
  label: string
  icon: IconName
  tone: string
  shortcut?: string
}

export interface QuickActionSection {
  label: string
  items: QuickActionItem[]
}
