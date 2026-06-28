'use client'
import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useRefreshWeekly, useWeekly } from '@/hooks/useWeekly'
import { StatGrid } from '@/components/weekly/StatGrid'
import { ObservationCard } from '@/components/weekly/ObservationCard'
import { WeekPicker } from '@/components/weekly/WeekPicker'

export default function WeeklyPage() {
  const t = useTranslations('weekly')
  const [weekOf, setWeekOf] = useState<string | undefined>(undefined)
  const { data } = useWeekly(weekOf)
  const refresh = useRefreshWeekly()

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
        <div className="flex items-center gap-2">
          <WeekPicker value={weekOf} onChange={setWeekOf} />
          <button
            onClick={() => refresh.mutate(weekOf)}
            disabled={refresh.isPending}
            className="inline-flex h-8 items-center gap-1 border border-black bg-black px-3 text-sm text-white hover:bg-neutral-800 disabled:opacity-40"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            {refresh.isPending ? t('refreshing') : t('refresh')}
          </button>
        </div>
      </div>
      {data && (
        <>
          <StatGrid stats={data.stats} />
          <ObservationCard text={data.ai_observation_text} actions={data.suggested_actions} />
        </>
      )}
    </div>
  )
}
