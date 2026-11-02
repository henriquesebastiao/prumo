import { expect, test } from '@playwright/test'

import { mockApi, settle } from './fixtures'

/**
 * Captures the screens that have a counterpart in design/v1/ into e2e/output/. `make screenshots`
 * then builds side-by-side images (design | implementation) in e2e/output/compare/.
 */
const OUT = 'e2e/output'

for (const theme of ['light', 'dark'] as const) {
  test(`login ${theme}`, async ({ page }) => {
    await mockApi(page, { authenticated: false, theme })
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/entrar')
    await page.getByLabel('Usuário').fill('henrique')
    await page.getByLabel('Senha', { exact: true }).fill('prumo-demo-01')
    await settle(page)
    await page.screenshot({ path: `${OUT}/login-${theme}.png` })
  })

  test(`home ${theme}`, async ({ page }) => {
    await mockApi(page, { theme })
    await page.setViewportSize({ width: 1440, height: 1160 })
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Boa tarde, Henrique' })).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/home-${theme}.png` })
  })

  test(`settings ${theme}`, async ({ page }) => {
    await mockApi(page, { theme })
    await page.setViewportSize({ width: 1440, height: 1180 })
    await page.goto('/configuracoes')
    await expect(page.getByText('Firefox · Linux')).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/settings-${theme}.png`, fullPage: true })
  })

  test(`composition home ${theme}`, async ({ page }) => {
    await mockApi(page, { theme })
    await page.setViewportSize({ width: 1440, height: 1160 })
    await page.goto(`/dev/ui?view=home&theme=${theme}`)
    await settle(page)
    await page.screenshot({ path: `${OUT}/composition-home-${theme}.png` })
  })
}

test('home mobile', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Boa tarde, Henrique' })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/home-mobile.png` })
})

test('composition states', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 1440, height: 1160 })
  await page.goto('/dev/ui?view=states&theme=light')
  await settle(page)
  await page.screenshot({ path: `${OUT}/composition-states-light.png` })
})

test('showcase', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  for (const theme of ['light', 'dark']) {
    await page.goto(`/dev/ui?theme=${theme}`)
    await settle(page)
    await page.screenshot({ path: `${OUT}/showcase-${theme}.png`, fullPage: true })
  }
  await page.setViewportSize({ width: 2560, height: 1000 })
  await page.goto('/dev/ui')
  await settle(page)
  await page.screenshot({ path: `${OUT}/showcase-both.png`, fullPage: true })
})
