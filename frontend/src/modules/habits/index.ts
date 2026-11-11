import { defineModule } from '@/app/registry'

import { routes } from './routes'

export default defineModule({
  id: 'habits',
  icon: 'list-checks',
  nav: { labelKey: 'habits.nav', route: 'habits.home' },
  descriptionKey: 'habits.description',
  routes,
  dashboardWidget: () => import('./widgets/HabitsWidget.vue'),
  quickActions: [
    {
      id: 'habits.check-in',
      labelKey: 'habits.actions.checkIn',
      chipLabelKey: 'habits.actions.checkInShort',
      icon: 'list-checks',
      shortcut: 'H',
      component: () => import('./forms/CheckInDialog.vue'),
    },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
})
