import { test, expect } from '@playwright/test'

test('resources page renders sidebar + new resource button', async ({ page }) => {
  await page.goto('/zh/resources')
  await expect(page.getByRole('heading', { name: '我的资源库' })).toBeVisible()
  await expect(page.getByRole('button', { name: '新资源' })).toBeVisible()
})
