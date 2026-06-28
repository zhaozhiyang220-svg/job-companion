import { test, expect } from '@playwright/test'

test('weekly page renders header and picker', async ({ page }) => {
  await page.goto('/zh/weekly')
  await expect(page.getByRole('heading', { name: '本周复盘' })).toBeVisible()
})
