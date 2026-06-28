import { test, expect } from '@playwright/test'

// 未登录时 API 报错，data 为 undefined，简历定制 Tab 仍渲染壳：
// JD 解读面板 + 「生成第一版定制简历」按钮。
test('resume customization tab renders generate button', async ({ page }) => {
  await page.goto('/zh/opportunities/test-id/resume')
  await expect(page.getByRole('button', { name: '生成第一版定制简历' })).toBeVisible()
})
