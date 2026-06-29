'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Events } from '@jc/shared-types'
import { track } from '@/lib/posthog'
import type { ApplicationListItem } from '@/hooks/useApplications'

export function OpportunityCard({ item }: { item: ApplicationListItem }) {
  const t = useTranslations('opportunities')
  const { locale } = useParams<{ locale: string }>()
  return (
    <Link
      href={`/${locale}/opportunities/${item.id}`}
      onClick={() => track(Events.OPPORTUNITY_OPENED, { id: item.id })}
      className="block border border-border p-4 transition-colors hover:border-fg"
    >
      <div className="flex items-center justify-between gap-2">
        <strong className="truncate">
          {item.company_name || t('no_company')} · {item.job_title}
        </strong>
        <span className="flex-shrink-0 font-mono text-xs text-fg-subtle">{item.status}</span>
      </div>
      <div className="text-sm text-fg-muted">
        {item.department} · {item.salary_range}
      </div>
      <div className="text-xs text-fg-subtle">
        {t('updated_at', { date: new Date(item.last_active_at).toLocaleDateString() })}
      </div>
    </Link>
  )
}
