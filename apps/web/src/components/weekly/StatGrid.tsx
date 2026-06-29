'use client'
import { useTranslations } from 'next-intl'
import type { WeeklyStats } from '@/hooks/useWeekly'

export function StatGrid({ stats }: { stats: WeeklyStats }) {
  const t = useTranslations('weekly')
  const cells = [
    { k: 'new_applications', v: stats.new_applications ?? 0 },
    { k: 'new_branches', v: stats.new_branches ?? 0 },
    { k: 'exports', v: stats.exports ?? 0 },
    { k: 'coach_inquiries', v: stats.coach_inquiries ?? 0 },
    { k: 'total_active', v: stats.total_active_applications ?? 0 },
  ]
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
      {cells.map((c) => (
        <div key={c.k} className="border border-border p-4 text-center">
          <div className="text-3xl font-bold tabular-nums">{c.v}</div>
          <div className="mt-1 text-xs text-fg-subtle">{t(`stat_${c.k}`)}</div>
        </div>
      ))}
    </div>
  )
}
