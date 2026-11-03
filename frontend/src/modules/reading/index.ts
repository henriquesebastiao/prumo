import { defineModule } from '@/app/registry'

import { describeActivity } from './events'
import { routes } from './routes'

export default defineModule({
  id: 'reading',
  icon: 'book',
  nav: { labelKey: 'reading.nav', route: 'reading.home' },
  descriptionKey: 'reading.description',
  routes,
  dashboardWidget: () => import('./widgets/ReadingWidget.vue'),
  quickActions: [
    {
      id: 'reading.update-page',
      labelKey: 'reading.actions.updatePage',
      chipLabelKey: 'reading.actions.pageRead',
      icon: 'bookmark',
      shortcut: 'P',
      pinned: 1,
      component: () => import('./forms/UpdatePageDialog.vue'),
    },
    {
      id: 'reading.add-note',
      labelKey: 'reading.actions.newNote',
      icon: 'note',
      shortcut: 'L',
      component: () => import('./forms/NoteDialog.vue'),
    },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
  describeActivity,
})
