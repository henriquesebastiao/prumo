import { defineConfig, devices } from '@playwright/test'

const port = 5174
const apiPort = 8001

/**
 * Screenshots for comparison with design/v1/ (`make screenshots`), captured at 2× like the design
 * exports. Platform screens mock the API (e2e/fixtures.ts); module screens use a real API seeded
 * with the design data and frozen at the design moment (backend/scripts/e2e_server.py).
 */
export default defineConfig({
  testDir: 'e2e',
  outputDir: 'test-results',
  fullyParallel: true,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
    reducedMotion: 'reduce',
    // Native date and time inputs follow the browser language, not the page locale.
    launchOptions: { args: ['--lang=pt-BR'] },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], deviceScaleFactor: 2 } }],
  webServer: [
    {
      command: 'uv run python scripts/e2e_server.py',
      cwd: '../backend',
      url: `http://127.0.0.1:${apiPort}/api/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: `pnpm exec vite --host 127.0.0.1 --port ${port} --strictPort`,
      url: `http://127.0.0.1:${port}`,
      env: { PRUMO_API_URL: `http://127.0.0.1:${apiPort}` },
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})
