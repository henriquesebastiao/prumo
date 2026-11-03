import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/financas',
    component: () => import('./pages/FinancePage.vue'),
    children: [
      { path: '', name: 'finance.home', component: () => import('./pages/OverviewTab.vue') },
      {
        path: 'transacoes',
        name: 'finance.transactions',
        component: () => import('./pages/TransactionsTab.vue'),
      },
      {
        path: 'contas',
        name: 'finance.accounts',
        component: () => import('./pages/AccountsTab.vue'),
      },
      {
        path: 'cartoes',
        name: 'finance.cards',
        component: () => import('./pages/CardsTab.vue'),
      },
      {
        path: 'categorias',
        name: 'finance.categories',
        component: () => import('./pages/CategoriesTab.vue'),
      },
    ],
  },
]
