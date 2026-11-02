import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'

import {
  activeModules,
  defineModule,
  findQuickAction,
  moduleRoutes,
  orderedModules,
  quickActionGroups,
} from './registry'

const Empty = defineComponent({ render: () => null })
const lazy = async () => ({ default: Empty })

const tasks = defineModule({
  id: 'tasks',
  icon: 'check',
  nav: { labelKey: 'tasks.nav', route: 'tasks.home' },
  routes: [{ path: '/tarefas', name: 'tasks.home', component: Empty }],
  quickActions: [
    { id: 'tasks.add', labelKey: 'tasks.add', icon: 'add', shortcut: 'T', component: lazy },
  ],
  messages: {},
})
const notes = defineModule({
  id: 'notes',
  icon: 'note',
  nav: { labelKey: 'notes.nav', route: 'notes.home' },
  routes: [{ path: '/notas', name: 'notes.home', component: Empty }],
  messages: {},
})

const api = [
  { id: 'notes', version: '1', enabled: true, position: 1 },
  { id: 'tasks', version: '1', enabled: false, position: 0 },
  { id: 'backend-only', version: '1', enabled: true, position: 2 },
]

describe('module registry', () => {
  it('orders modules like the API and drops unknown ones', () => {
    const ordered = orderedModules([tasks, notes], api)
    expect(ordered.map((state) => [state.definition.id, state.enabled])).toEqual([
      ['tasks', false],
      ['notes', true],
    ])
    expect(orderedModules([tasks, notes], undefined)).toEqual([])
  })

  it('keeps only enabled modules active', () => {
    expect(activeModules([tasks, notes], api).map((module) => module.id)).toEqual(['notes'])
  })

  it('tags routes with their module', () => {
    expect(moduleRoutes([tasks, notes]).map((route) => route.meta?.module)).toEqual([
      'tasks',
      'notes',
    ])
  })

  it('groups quick actions by active module', () => {
    const enabled = [tasks, notes]
    expect(quickActionGroups(enabled).map((group) => group.module.id)).toEqual(['tasks'])
    expect(findQuickAction(enabled, 'tasks.add')?.shortcut).toBe('T')
    expect(findQuickAction(enabled, 'missing')).toBeUndefined()
  })
})
