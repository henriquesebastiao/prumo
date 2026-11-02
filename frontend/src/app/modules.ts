import { computed } from 'vue'

import { installedModules } from '@/modules'
import { useModules } from '@/system/api'

import { activeModules, orderedModules, quickActionGroups } from './registry'

/** Installed front-end modules, ordered and filtered by the user's preferences. */
export function useActiveModules() {
  const query = useModules()
  const ordered = computed(() => orderedModules(installedModules, query.data.value))
  const active = computed(() => activeModules(installedModules, query.data.value))
  const quickActions = computed(() => quickActionGroups(active.value))
  return { query, ordered, active, quickActions }
}
