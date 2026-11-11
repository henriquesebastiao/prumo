import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/**
 * Estudos screens against the seeded API (backend/scripts/e2e_server.py). There is no design
 * board for this module: the captures are for review in both themes.
 */
const OUT = 'e2e/output'

test.describe.configure({ mode: 'serial' })

async function signIn(page: Page, theme: 'light' | 'dark' = 'light') {
  await page.clock.setFixedTime(DESIGN_NOW)
  await page.emulateMedia({ colorScheme: theme })
  await page.addInitScript(() => localStorage.setItem('prumo.theme', 'system'))
  const response = await page.request.post('/api/v1/auth/login', {
    data: { username: 'henrique', password: 'prumo-demo-01', client: 'web' },
  })
  expect(response.ok()).toBeTruthy()
}

async function subjectId(page: Page, name: string): Promise<string> {
  const response = await page.request.get('/api/v1/studies/subjects')
  const body = (await response.json()) as { items: { id: string; name: string }[] }
  return body.items.find((subject) => subject.name === name)!.id
}

for (const theme of ['light', 'dark'] as const) {
  test(`today ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/estudos')
    await expect(page.getByText('FastAPI').first()).toBeVisible()
    await expect(page.getByText('Em andamento').first()).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/studies-today-${theme}.png` })
  })

  test(`week ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 1400 })
    await page.goto('/estudos/semana')
    await expect(page.getByText('Esta semana')).toBeVisible()
    await page.getByRole('button', { name: 'Semana anterior' }).click()
    await expect(page.getByText('Dia perdido')).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/studies-week-${theme}.png`, fullPage: true })
  })
}

test('subjects and plan', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/estudos/materias')
  await expect(page.getByText('Estruturas de Dados')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/studies-subjects.png`, fullPage: true })
  await page.goto('/estudos/plano')
  await expect(page.getByText('Vigente desde 02/11/2026')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/studies-plan.png`, fullPage: true })
})

test('subject detail', async ({ page }) => {
  await signIn(page)
  const id = await subjectId(page, 'FastAPI')
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(`/estudos/materias/${id}`)
  await expect(page.getByText('Minutos por semana')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Abrir no Obsidian' })).toHaveAttribute(
    'href',
    /^obsidian:\/\//,
  )
  await settle(page)
  await page.screenshot({ path: `${OUT}/studies-subject.png`, fullPage: true })
})

test('log a session from the quick action', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 800 })
  await page.goto('/')
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await page.keyboard.press('n')
  await expect(page.getByRole('listbox')).toBeFocused()
  await page.keyboard.press('E')
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await expect(page.getByRole('radio', { name: '30 min' })).toBeChecked()
  await settle(page)
  await page.screenshot({ path: `${OUT}/studies-dialog-session.png` })
})

test('plan dialog', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/estudos/plano')
  await expect(page.getByText('Vigente desde 02/11/2026')).toBeVisible()
  await page.getByRole('button', { name: 'Mudar o plano' }).click()
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/studies-dialog-plan.png` })
})
