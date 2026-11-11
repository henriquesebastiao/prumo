import type { RouteRecordRaw } from 'vue-router'

const UUID = '[0-9a-f-]{36}'

export const routes: RouteRecordRaw[] = [
  {
    path: '/habitos',
    component: () => import('./pages/HabitsPage.vue'),
    children: [
      { path: '', name: 'habits.home', component: () => import('./pages/TodayTab.vue') },
      { path: 'lista', name: 'habits.list', component: () => import('./pages/ListTab.vue') },
    ],
  },
  {
    path: `/habitos/:habitId(${UUID})`,
    name: 'habits.habit',
    component: () => import('./pages/HabitDetailPage.vue'),
    props: true,
  },
]
