import { test, expect } from '@playwright/test'

// 未登录时 API 报错，投递记录 Tab 仍渲染壳：标题 + 「新增动作」按钮。
test('investments tab renders new-action button', async ({ page }) => {
  await page.goto('/zh/opportunities/test-id/investments')
  await expect(page.getByRole('button', { name: '新增动作' })).toBeVisible()
})
