import { defineModule } from '@/app/registry'

import { describeActivity, describeUpcoming } from './events'
import { routes } from './routes'

export default defineModule({
  id: 'garage',
  icon: 'car',
  nav: { labelKey: 'garage.nav', route: 'garage.home' },
  descriptionKey: 'garage.description',
  routes,
  dashboardWidget: () => import('./widgets/GarageWidget.vue'),
  quickActions: [
    {
      id: 'garage.update-km',
      labelKey: 'garage.actions.updateKm',
      icon: 'gauge',
      shortcut: 'K',
      pinned: 2,
      component: () => import('./forms/UpdateKmDialog.vue'),
    },
    {
      id: 'garage.add-fueling',
      labelKey: 'garage.actions.addFueling',
      chipLabelKey: 'garage.actions.fuel',
      icon: 'fuel',
      shortcut: 'A',
      pinned: 1,
      component: () => import('./forms/FuelingDialog.vue'),
    },
    {
      id: 'garage.add-oil-change',
      labelKey: 'garage.actions.addOilChange',
      icon: 'droplet',
      shortcut: 'O',
      component: () => import('./forms/OilChangeDialog.vue'),
    },
    {
      id: 'garage.add-maintenance',
      labelKey: 'garage.actions.addMaintenance',
      icon: 'wrench',
      shortcut: 'M',
      component: () => import('./forms/MaintenanceDialog.vue'),
    },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
  describeUpcoming,
  describeActivity,
})
