import type { ModuleDefinition } from '@/app/registry'

import finance from './finance'
import garage from './garage'
import reading from './reading'

/**
 * Front-end modules shipped with this build, in installation order (the default for new users):
 * finance, garage, reading. Each one is added in its phase of the ROADMAP.
 */
export const installedModules: ModuleDefinition[] = [finance, garage, reading]
