import { defineModule } from '@/app/registry'

import { describeActivity, describeUpcoming } from './events'
import { routes } from './routes'

export default defineModule({
  id: 'finance',
  icon: 'wallet',
  nav: { labelKey: 'finance.nav', route: 'finance.home' },
  descriptionKey: 'finance.description',
  routes,
  dashboardWidget: () => import('./widgets/FinanceWidget.vue'),
  quickActions: [
    {
      id: 'finance.add-expense',
      labelKey: 'finance.actionsQuick.addExpense',
      chipLabelKey: 'finance.actions.expense',
      icon: 'minus',
      shortcut: 'D',
      pinned: 1,
      component: () => import('./forms/ExpenseDialog.vue'),
    },
    {
      id: 'finance.add-income',
      labelKey: 'finance.actionsQuick.addIncome',
      chipLabelKey: 'finance.actions.income',
      icon: 'add',
      shortcut: 'R',
      pinned: 2,
      component: () => import('./forms/IncomeDialog.vue'),
    },
    {
      id: 'finance.add-transfer',
      labelKey: 'finance.actionsQuick.addTransfer',
      chipLabelKey: 'finance.actions.transfer',
      icon: 'transfer',
      shortcut: 'T',
      pinned: 3,
      component: () => import('./forms/TransferDialog.vue'),
    },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
  describeUpcoming,
  describeActivity,
})
