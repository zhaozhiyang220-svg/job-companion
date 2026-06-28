import { test, expect } from '@playwright/test'

test('coach page renders', async ({ page }) => {
  await page.goto('/zh/coach')
  await expect(page.getByRole('heading', { name: '找 Coach 锐评' })).toBeVisible()
})

test('internal dashboard requires password', async ({ page }) => {
  await page.goto('/internal/dashboard')
  await expect(page.getByPlaceholder('internal password')).toBeVisible()
})
