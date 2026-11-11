import type { RouteRecordRaw } from 'vue-router'

const UUID = '[0-9a-f-]{36}'

export const routes: RouteRecordRaw[] = [
  {
    path: '/estudos',
    component: () => import('./pages/StudiesPage.vue'),
    children: [
      { path: '', name: 'studies.home', component: () => import('./pages/TodayTab.vue') },
      { path: 'semana', name: 'studies.week', component: () => import('./pages/WeekTab.vue') },
      {
        path: 'materias',
        name: 'studies.subjects',
        component: () => import('./pages/SubjectsTab.vue'),
      },
      { path: 'plano', name: 'studies.plan', component: () => import('./pages/PlanTab.vue') },
    ],
  },
  {
    path: `/estudos/materias/:subjectId(${UUID})`,
    name: 'studies.subject',
    component: () => import('./pages/SubjectDetailPage.vue'),
    props: true,
  },
]
