import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/**
 * Hábitos screens against the seeded API (backend/scripts/e2e_server.py). There is no design
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

async function habitId(page: Page, name: string): Promise<string> {
  const response = await page.request.get('/api/v1/habits')
  const body = (await response.json()) as { items: { id: string; name: string }[] }
  return body.items.find((habit) => habit.name === name)!.id
}

for (const theme of ['light', 'dark'] as const) {
  test(`today ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/habitos')
    await expect(page.getByText('0 de 4 hoje')).toBeVisible()
    await expect(page.getByText('1 de 3 esta semana')).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/habits-today-${theme}.png` })
  })

  test(`habit ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    const id = await habitId(page, 'Ler a Bíblia')
    await page.setViewportSize({ width: 1440, height: 1200 })
    await page.goto(`/habitos/${id}`)
    await expect(page.getByText('40 dias').first()).toBeVisible()
    await expect(page.getByRole('grid', { name: 'Calendário' })).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/habits-habit-${theme}.png`, fullPage: true })
  })
}

test('list and a habit to quit', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/habitos/lista')
  await expect(page.getByText('Para abandonar')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/habits-list.png`, fullPage: true })
  await page.goto(`/habitos/${await habitId(page, 'Redes sociais antes de dormir')}`)
  await expect(page.getByText('Domingo entediado.')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/habits-quit.png`, fullPage: true })
})

test('mark and unmark today', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/habitos')
  const anki = page.getByRole('checkbox', { name: 'Marcar Anki' })
  await anki.check()
  await expect(page.getByText('1 de 4 hoje')).toBeVisible()
  await page.getByRole('checkbox', { name: 'Desmarcar Anki' }).uncheck()
  await expect(page.getByText('0 de 4 hoje')).toBeVisible()
})

test('check in from the quick action', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 800 })
  await page.goto('/')
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await page.keyboard.press('n')
  await expect(page.getByRole('listbox')).toBeFocused()
  await page.keyboard.press('H')
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await expect(page.getByText('Beber água').last()).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/habits-dialog-check-in.png` })
})

test('new habit dialog', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 1000 })
  await page.goto('/habitos')
  await page.getByRole('button', { name: 'Novo hábito' }).click()
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/habits-dialog-habit.png` })
})
