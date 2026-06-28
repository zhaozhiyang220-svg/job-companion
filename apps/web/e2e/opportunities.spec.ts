import { test, expect } from '@playwright/test'

test('opportunities page loads', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await expect(page.getByRole('heading', { name: '我的求职机会' })).toBeVisible()
  await expect(page.getByRole('button', { name: '新增机会' })).toBeVisible()
})

test('new opportunity dialog opens', async ({ page }) => {
  await page.goto('/zh/opportunities')
  await page.getByRole('button', { name: '新增机会' }).click()
  await expect(page.getByPlaceholder('粘贴 JD 文本')).toBeVisible()
})
