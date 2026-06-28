import { defineConfig, devices } from '@playwright/test'

// 本地 shell/系统注入了代理，会拦截 Playwright 对 localhost 的探活与导航。
// 在 e2e 运行进程内清掉代理，确保直连本地 dev server。
for (const key of [
  'all_proxy',
  'ALL_PROXY',
  'http_proxy',
  'HTTP_PROXY',
  'https_proxy',
  'HTTPS_PROXY',
]) {
  delete process.env[key]
}
process.env.NO_PROXY = '*'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  retries: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    // 系统 Chrome 会按系统代理路由 localhost，强制直连。
    launchOptions: { args: ['--no-proxy-server', '--proxy-bypass-list=*'] },
  },
  // 本地可设 PW_CHANNEL=chrome 直接用系统 Chrome（免下载 chromium）；
  // CI 不设此变量，使用 `playwright install` 下载的 chromium。
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        ...(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}),
      },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://127.0.0.1:3000',
    timeout: 180_000,
    reuseExistingServer: !process.env.CI,
  },
})
