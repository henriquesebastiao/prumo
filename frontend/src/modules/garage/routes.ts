import type { RouteRecordRaw } from 'vue-router'

const UUID = '[0-9a-f-]{36}'

export const routes: RouteRecordRaw[] = [
  {
    path: '/veiculos',
    component: () => import('./pages/GaragePage.vue'),
    children: [
      { path: '', name: 'garage.home', component: () => import('./pages/VehiclesTab.vue') },
      {
        path: 'abastecimentos',
        name: 'garage.fuelings',
        component: () => import('./pages/FuelingsTab.vue'),
      },
      {
        path: 'manutencoes',
        name: 'garage.maintenances',
        component: () => import('./pages/MaintenancesTab.vue'),
        props: { kind: 'general' },
      },
      {
        path: 'trocas-de-oleo',
        name: 'garage.oil-changes',
        component: () => import('./pages/MaintenancesTab.vue'),
        props: { kind: 'oil_change' },
      },
      {
        path: 'oficinas',
        name: 'garage.workshops',
        component: () => import('./pages/WorkshopsTab.vue'),
      },
    ],
  },
  {
    path: `/veiculos/:vehicleId(${UUID})`,
    name: 'garage.vehicle',
    component: () => import('./pages/VehicleDetailPage.vue'),
    props: true,
  },
  {
    path: `/veiculos/:vehicleId(${UUID})/manutencoes/:maintenanceId(${UUID})`,
    name: 'garage.maintenance',
    component: () => import('./pages/MaintenanceDetailPage.vue'),
    props: true,
  },
]
