import '@/design/index.css'

import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { onUnauthorized } from '@/lib/api/client'
import { installedModules } from '@/modules'

import App from './App.vue'
import { i18n, loadModuleMessages } from './i18n'
import { queryClient } from './query'
import { router } from './router'
import { useSessionStore } from './stores/session'
import { useThemeStore } from './stores/theme'

async function start() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(i18n)
  app.use(VueQueryPlugin, { queryClient })
  app.use(router)
  useThemeStore()
  await loadModuleMessages(installedModules)

  // Session ended while using the app (expired or revoked elsewhere): back to the login.
  const session = useSessionStore(pinia)
  onUnauthorized(() => {
    if (session.status !== 'authenticated') return
    session.clear()
    const current = router.currentRoute.value
    if (!current.meta.public) {
      void router.replace({ name: 'login', query: { next: current.fullPath } })
    }
  })

  app.mount('#app')
}

void start()
