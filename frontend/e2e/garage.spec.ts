import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/** Garage screens against the seeded API (backend/scripts/e2e_server.py). */
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

async function vehicleIds(page: Page): Promise<Record<string, string>> {
  const response = await page.request.get('/api/v1/garage/vehicles')
  const body = (await response.json()) as { items: { id: string; name: string }[] }
  return Object.fromEntries(body.items.map((vehicle) => [vehicle.name, vehicle.id]))
}

for (const theme of ['light', 'dark'] as const) {
  test(`home with garage ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 1160 })
    await page.goto('/')
    await expect(page.getByText('Próxima troca de óleo')).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/garage-home-${theme}.png` })
  })

  test(`vehicles list ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 1000 })
    await page.goto('/veiculos')
    await expect(page.getByText('Fiat Strada Freedom').first()).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/garage-list-${theme}.png` })
  })
}

test('vehicle detail', async ({ page }) => {
  await signIn(page)
  const ids = await vehicleIds(page)
  await page.setViewportSize({ width: 1440, height: 1240 })
  await page.goto(`/veiculos/${ids['Honda CG 160 Fan']}`)
  await expect(page.getByText('Próxima troca de óleo')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/garage-detail.png` })
})

test('maintenance detail', async ({ page }) => {
  await signIn(page)
  const ids = await vehicleIds(page)
  const list = await page.request.get(
    `/api/v1/garage/maintenances?vehicle_id=${ids['Honda CG 160 Fan']}&kind=general`,
  )
  const body = (await list.json()) as { items: { id: string; km: number }[] }
  const target = body.items.find((item) => item.km === 16180)!
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(`/veiculos/${ids['Honda CG 160 Fan']}/manutencoes/${target.id}`)
  await expect(page.getByText('Peças e serviços')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/garage-maintenance.png` })
})

const dialogs = [
  { name: 'maintenance', key: 'M', height: 1240 },
  { name: 'fueling', key: 'A', height: 1000 },
  { name: 'oil', key: 'O', height: 1000 },
  { name: 'km', key: 'K', height: 720 },
]

for (const dialog of dialogs) {
  test(`dialog ${dialog.name}`, async ({ page }) => {
    await signIn(page)
    await page.setViewportSize({ width: 1280, height: dialog.height })
    await page.goto('/')
    await expect(page.getByText('Próxima troca de óleo')).toBeVisible()
    await page.keyboard.press('n')
    await expect(page.getByRole('listbox')).toBeFocused()
    await page.keyboard.press(dialog.key)
    await expect(page.locator('.p-dialog--modal')).toBeVisible()
    await expect(page.locator('.p-popover')).toHaveCount(0)
    await settle(page)
    await page.screenshot({ path: `${OUT}/garage-dialog-${dialog.name}.png` })
  })
}

test('vehicle edit dialog', async ({ page }) => {
  await signIn(page)
  const ids = await vehicleIds(page)
  await page.setViewportSize({ width: 1280, height: 1000 })
  await page.goto(`/veiculos/${ids['Honda CG 160 Fan']}`)
  await page.getByRole('button', { name: 'Editar', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/garage-dialog-vehicle.png` })
})

test('home phone', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 390, height: 1720 })
  await page.goto('/')
  await expect(page.getByText('Próxima troca de óleo')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/garage-home-phone.png` })
})
