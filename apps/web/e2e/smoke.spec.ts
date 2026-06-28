import { test, expect } from '@playwright/test'

test('zh home loads', async ({ page }) => {
  await page.goto('/zh')
  await expect(page.getByRole('heading', { name: '求职作战中心' })).toBeVisible()
})

test('en home loads', async ({ page }) => {
  await page.goto('/en')
  await expect(page.getByRole('heading', { name: 'Job Companion' })).toBeVisible()
})

test('login page reachable', async ({ page }) => {
  await page.goto('/zh/login')
  await expect(page.getByRole('button', { name: '发送登录链接' })).toBeVisible()
})

test('disguise toggle changes title', async ({ page }) => {
  await page.goto('/zh/dashboard')
  await page.keyboard.press('Control+`')
  await expect(page).toHaveTitle(/TimeFlow/)
  await page.keyboard.press('Control+`')
  await expect(page).toHaveTitle(/Job Companion/)
})
