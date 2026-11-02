/**
 * Front-end module contract (mirrors PrumoModule in the backend). A module declares its routes,
 * navigation entry, Início widget, quick actions and texts; the app assembles them following the
 * enabled modules and the order returned by GET /api/v1/modules.
 */
import type { Component } from 'vue'
import type { RouteRecordRaw } from 'vue-router'

import type { Schemas } from '@/lib/api/client'
import type { IconName } from '@/ui'

type Lazy = () => Promise<{ default: Component }>

export interface QuickAction {
  /** `<module>.<action>`, e.g. `garage.update-km`. */
  id: string
  labelKey: string
  icon: IconName
  /** Single key that runs the action while the Registrar menu is open. */
  shortcut?: string
  /** Shown as a chip at the top of Início. */
  pinned?: boolean
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
