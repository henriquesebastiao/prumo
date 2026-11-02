import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import AppShell from '@/layouts/AppShell.vue'
import { installedModules } from '@/modules'

import { moduleRoutes } from './registry'
import { useSessionStore } from './stores/session'

declare module 'vue-router' {
  interface RouteMeta {
    /** Reachable without a session. */
    public?: boolean
    /** Module that owns the route (navigation highlight). */
    module?: string
  }
}

const devRoutes: RouteRecordRaw[] = import.meta.env.DEV
  ? [
      {
        path: '/dev/ui',
        name: 'dev.ui',
        component: () => import('@/system/dev-ui/DevUiPage.vue'),
        meta: { public: true },
      },
    ]
  : []

export const routes: RouteRecordRaw[] = [
  {
    path: '/entrar',
    name: 'login',
    component: () => import('@/system/login/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', name: 'home', component: () => import('@/system/home/HomePage.vue') },
      {
        path: 'configuracoes',
        name: 'settings',
        component: () => import('@/system/settings/SettingsPage.vue'),
      },
      ...moduleRoutes(installedModules),
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('@/system/errors/NotFoundPage.vue'),
      },
    ],
  },
  ...devRoutes,
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, saved) {
    if (saved) return saved
    if (to.hash) return { el: to.hash, behavior: 'smooth', top: 16 }
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  await session.load().catch(() => undefined)
  if (to.meta.public) {
    return to.name === 'login' && session.status === 'authenticated' ? { name: 'home' } : true
  }
  if (session.status !== 'authenticated') {
    return { name: 'login', query: to.fullPath === '/' ? {} : { next: to.fullPath } }
  }
  return true
})
