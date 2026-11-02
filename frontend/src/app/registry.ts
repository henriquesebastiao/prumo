/**
 * Front-end module contract (mirrors PrumoModule in the backend). A module declares its routes,
 * navigation entry, Início widget, quick actions and texts; the app assembles them following the
 * enabled modules and the order returned by GET /api/v1/modules.
 */
import type { Component } from 'vue'
import type { RouteLocationRaw, RouteRecordRaw } from 'vue-router'

import type { Schemas } from '@/lib/api/client'
import type { i18n } from './i18n'
import type { IconName } from '@/ui'

type Lazy = () => Promise<{ default: Component }>

export type Translate = typeof i18n.global.t

/** How Início shows one "Vem aí" or "Atividade recente" item of a module. */
export interface EventView {
  title: string
  subtitle?: string
  /** Value at the right (activity): `18.420 km`, `R$ 46,36`. */
  value?: string
  icon?: IconName
  to?: RouteLocationRaw
}

export interface QuickAction {
  /** `<module>.<action>`, e.g. `garage.update-km`. */
  id: string
  labelKey: string
  icon: IconName
  /** Single key that runs the action while the Registrar menu is open. */
  shortcut?: string
  /** Shown as a chip at the top of Início; a number sets the order among the chips. */
  pinned?: boolean | number
  /** Shorter label for the chip ("Abastecer" instead of "Abastecimento"). */
  chipLabelKey?: string
  component: Lazy
}

export interface ModuleDefinition {
  /** Same id as the backend module. Also its color tone (`--color-module-<id>`). */
  id: string
  icon: IconName
  nav: { labelKey: string; route: string }
  descriptionKey?: string
  routes: RouteRecordRaw[]
  /** Receives the module's dashboard summary as the `summary` prop. */
  dashboardWidget?: Lazy
  quickActions?: QuickAction[]
  messages: Partial<Record<string, () => Promise<{ default: Record<string, unknown> }>>>
  /** Describes the module's `upcoming` items of GET /dashboard (by `kind`). */
  describeUpcoming?: (item: Schemas['UpcomingItem'], t: Translate) => EventView | null
  /** Describes the module's `activity` items of GET /dashboard (by `kind`). */
  describeActivity?: (item: Schemas['ActivityItem'], t: Translate) => EventView | null
}

export function defineModule(definition: ModuleDefinition): ModuleDefinition {
  return definition
}

/** Routes of every installed module, marked with their module (used for navigation state). */
export function moduleRoutes(modules: ModuleDefinition[]): RouteRecordRaw[] {
  return modules.flatMap((module) =>
    module.routes.map((route) => ({ ...route, meta: { ...route.meta, module: module.id } })),
  )
}

export interface ModuleState {
  definition: ModuleDefinition
  enabled: boolean
}

/**
 * Front-end modules in the user's order. Modules the API does not know, or the front end does
 * not ship, are left out.
 */
export function orderedModules(
  installed: ModuleDefinition[],
  apiModules: Schemas['ModuleRead'][] | undefined,
): ModuleState[] {
  if (!apiModules) return []
  return [...apiModules]
    .sort((a, b) => a.position - b.position)
    .flatMap((item) => {
      const definition = installed.find((module) => module.id === item.id)
      return definition ? [{ definition, enabled: item.enabled }] : []
    })
}

export function activeModules(
  installed: ModuleDefinition[],
  apiModules: Schemas['ModuleRead'][] | undefined,
): ModuleDefinition[] {
  return orderedModules(installed, apiModules)
    .filter((state) => state.enabled)
    .map((state) => state.definition)
}

export interface QuickActionGroup {
  module: ModuleDefinition
  actions: QuickAction[]
}

export function quickActionGroups(active: ModuleDefinition[]): QuickActionGroup[] {
  return active
    .filter((module) => (module.quickActions?.length ?? 0) > 0)
    .map((module) => ({ module, actions: module.quickActions ?? [] }))
}

export function findQuickAction(active: ModuleDefinition[], id: string): QuickAction | undefined {
  return active.flatMap((module) => module.quickActions ?? []).find((action) => action.id === id)
}
