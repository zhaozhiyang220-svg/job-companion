import { test, expect } from '@playwright/test'

// 未登录时 API 返回 401，react-query 报错但 data 为 undefined，
// 页面仍渲染标题 + 模式选择（上传 / AI 挖经历）。
test('master-resume page renders mode chooser when empty', async ({ page }) => {
  await page.goto('/zh/master-resume')
  await expect(page.getByRole('heading', { name: '我的主简历' })).toBeVisible()
  await expect(page.getByText('上传简历')).toBeVisible()
})
