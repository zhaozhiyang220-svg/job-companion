export type DashboardSummary = {
  dau: number
  mau: number
  total_users: number
  ai_calls_today: number
  ai_cost_today_usd: number
  ai_calls_30d: number
  ai_cost_30d_usd: number
  coach_inquiries_week: number
}

export type DailyRow = {
  date: string
  dau: number
  ai_calls: number
  ai_cost: number
}
