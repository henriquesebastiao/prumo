import type { Page, Route } from '@playwright/test'

/** Fixed moment of the design boards: Tuesday, 17 Nov 2026, 14:30 in São Paulo. */
export const DESIGN_NOW = new Date('2026-11-17T17:30:00Z')

export const user = {
  id: '01a19c92-845a-7364-9d06-1e41be8d7dd8',
  username: 'henrique',
  display_name: 'Henrique Sebastião',
  is_admin: true,
  created_at: '2026-11-01T12:00:00Z',
  updated_at: '2026-11-01T12:00:00Z',
}

export function preferences(theme: 'light' | 'dark' | 'system' = 'light') {
  return {
    theme,
    locale: 'pt-BR',
    timezone: 'America/Sao_Paulo',
    currency: 'BRL',
    enabled_modules: [],
    created_at: '2026-11-01T12:00:00Z',
    updated_at: '2026-11-01T12:00:00Z',
  }
}

const sessions = {
  items: [
    {
      id: '01a19c92-91ac-7514-8446-5b73eed946a5',
      client: 'web',
      device_name: 'Firefox · Linux',
      current: true,
      last_used_at: '2026-11-17T10:42:00Z',
      expires_at: '2026-12-17T10:42:00Z',
      created_at: '2026-11-17T10:42:00Z',
      updated_at: '2026-11-17T10:42:00Z',
    },
    {
      id: '01a19c92-921e-7564-9f3d-abd4e89a95f2',
      client: 'app',
      device_name: 'Pixel 8',
      current: false,
      last_used_at: '2026-11-16T21:10:00Z',
      expires_at: '2027-05-15T21:10:00Z',
      created_at: '2026-11-01T12:00:00Z',
      updated_at: '2026-11-16T21:10:00Z',
    },
  ],
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

interface MockOptions {
  authenticated?: boolean
  theme?: 'light' | 'dark' | 'system'
}

/** Mocks the API at /api/** and freezes the clock at the design moment. */
export async function mockApi(
  page: Page,
  { authenticated = true, theme = 'light' }: MockOptions = {},
) {
  await page.clock.setFixedTime(DESIGN_NOW)
  await page.addInitScript((value) => localStorage.setItem('prumo.theme', value), theme)
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const url = new URL(route.request().url())
      const method = route.request().method()
      const path = url.pathname
      if (path === '/api/v1/me' && !authenticated) {
        return json(
          route,
          { error: { code: 'auth.required', message: 'Authentication required.' } },
          401,
        )
      }
      if (path === '/api/v1/me') return json(route, user)
      if (path === '/api/v1/me/preferences') return json(route, preferences(theme))
      if (path === '/api/v1/modules') return json(route, { items: [] })
      if (path === '/api/v1/dashboard') return json(route, { modules: [] })
      if (path === '/api/v1/auth/sessions') return json(route, sessions)
      if (method !== 'GET') return route.fulfill({ status: 204 })
      return json(route, { error: { code: 'not_found', message: 'Not found.' } }, 404)
    },
  )
}

export async function settle(page: Page) {
  await page.evaluate(() => document.fonts.ready)
  await page.waitForLoadState('networkidle')
}
