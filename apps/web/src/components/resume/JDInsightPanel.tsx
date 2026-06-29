'use client'
import { useTranslations } from 'next-intl'
import type { JobPosting } from '@/hooks/useApplications'
import { LinkedResourcesPanel } from './LinkedResourcesPanel'

export function JDInsightPanel({
  jp,
  matchScore,
  appId,
}: {
  jp: JobPosting | undefined
  matchScore: number | null
  appId: string
}) {
  const t = useTranslations('resume_tab')
  const reqs = jp?.requirements_parsed ?? {}
  return (
    <aside className="w-72 flex-shrink-0 space-y-3 border-r border-border pr-4 text-sm">
      <div>
        <div className="text-xs text-fg-subtle">{t('match_score')}</div>
        <div className="text-3xl font-bold tabular-nums">
          {matchScore ?? '—'} <span className="text-base">/ 100</span>
        </div>
      </div>
      <Block title={t('keywords')} items={[...(reqs.hard ?? []), ...(reqs.soft ?? [])]} />
      <Block title={t('preferences')} items={jp?.hidden_preferences ?? []} />
      <Block title={t('red_flags')} items={jp?.red_flags ?? []} />
      <LinkedResourcesPanel appId={appId} />
    </aside>
  )
}

function Block({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null
  return (
    <div>
      <div className="mb-1 font-semibold">{title}</div>
      <ul className="list-disc pl-5">
        {items.map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </div>
  )
}
