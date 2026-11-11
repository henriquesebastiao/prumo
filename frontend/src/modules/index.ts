import type { ModuleDefinition } from '@/app/registry'

import finance from './finance'
import garage from './garage'
import habits from './habits'
import reading from './reading'
import studies from './studies'

/**
 * Front-end modules shipped with this build, in installation order (the default for new users):
 * finance, garage, reading, studies, habits. Each one is added in its phase of the ROADMAP.
 */
export const installedModules: ModuleDefinition[] = [finance, garage, reading, studies, habits]
