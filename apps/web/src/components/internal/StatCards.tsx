'use client'
import type { DashboardSummary } from './types'

export function StatCards({ s }: { s: DashboardSummary }) {
  const cells: { k: string; v: string | number }[] = [
    { k: 'DAU', v: s.dau },
    { k: 'MAU', v: s.mau },
    { k: 'Total Users', v: s.total_users },
    { k: 'Coach (week)', v: s.coach_inquiries_week },
    { k: 'AI calls (today)', v: s.ai_calls_today },
    { k: 'AI cost (today)', v: `$${Number(s.ai_cost_today_usd).toFixed(2)}` },
    { k: 'AI calls (30d)', v: s.ai_calls_30d },
    { k: 'AI cost (30d)', v: `$${Number(s.ai_cost_30d_usd).toFixed(2)}` },
  ]
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {cells.map((c) => (
        <div key={c.k} className="border border-border p-3 text-center">
          <div className="text-xs text-fg-subtle">{c.k}</div>
          <div className="mt-1 text-2xl font-bold tabular-nums">{c.v}</div>
        </div>
      ))}
    </div>
  )
}
