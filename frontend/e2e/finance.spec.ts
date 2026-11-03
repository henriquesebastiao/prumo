import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/** Finanças screens against the seeded API (backend/scripts/e2e_server.py). */
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

for (const theme of ['light', 'dark'] as const) {
  test(`overview ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 1300 })
    await page.goto('/financas')
    await expect(page.getByText('Saldo por conta')).toBeVisible()
    await expect(page.getByText('Supermercado').first()).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/finance-overview-${theme}.png` })
  })
}

test('transactions', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1460 })
  await page.goto('/financas/transacoes')
  await expect(page.getByText('Padaria', { exact: true })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/finance-transactions.png` })
})

test('accounts with the new account panel', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/financas/contas')
  await expect(page.getByText('Suas contas')).toBeVisible()
  await page.getByRole('button', { name: 'Nova conta' }).click()
  await expect(page.getByRole('heading', { name: 'Nova conta' })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/finance-accounts.png` })
})

test('cards', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1160 })
  await page.goto('/financas/cartoes')
  await expect(page.getByText('Faturas anteriores')).toBeVisible()
  await expect(page.getByText('Restaurante')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/finance-cards.png` })
})

test('categories while editing', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/financas/categorias')
  await page.getByRole('button', { name: 'Editar Combustível' }).click()
  await expect(page.getByRole('heading', { name: 'Editar categoria' })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/finance-categories.png` })
})

for (const dialog of [
  { name: 'expense', key: 'D' },
  { name: 'transfer', key: 'T' },
]) {
  test(`dialog ${dialog.name}`, async ({ page }) => {
    await signIn(page)
    await page.setViewportSize({ width: 1280, height: 1000 })
    await page.goto('/')
    await expect(page.getByText('Saldo total').first()).toBeVisible()
    await page.keyboard.press('n')
    await expect(page.getByRole('listbox')).toBeFocused()
    await page.keyboard.press(dialog.key)
    await expect(page.locator('.p-dialog--modal')).toBeVisible()
    await expect(page.locator('.p-popover')).toHaveCount(0)
    await settle(page)
    await page.screenshot({ path: `${OUT}/finance-dialog-${dialog.name}.png` })
  })
}

test('home with finance', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1160 })
  await page.goto('/')
  await expect(page.getByText('Gastos por categoria')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/finance-home-light.png` })
})
