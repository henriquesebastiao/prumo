import { defineModule } from '@/app/registry'

import { describeActivity } from './events'
import { routes } from './routes'

export default defineModule({
  id: 'studies',
  icon: 'graduation-cap',
  nav: { labelKey: 'studies.nav', route: 'studies.home' },
  descriptionKey: 'studies.description',
  routes,
  dashboardWidget: () => import('./widgets/StudiesWidget.vue'),
  quickActions: [
    {
      id: 'studies.log-session',
      labelKey: 'studies.actions.logSession',
      chipLabelKey: 'studies.actions.logSessionShort',
      icon: 'graduation-cap',
      shortcut: 'E',
      component: () => import('./forms/SessionDialog.vue'),
    },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
  describeActivity,
})
