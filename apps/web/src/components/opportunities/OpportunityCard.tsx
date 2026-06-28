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
      className="block border border-neutral-200 p-4 transition-colors hover:border-black"
    >
      <div className="flex items-center justify-between gap-2">
        <strong className="truncate">
          {item.company_name || t('no_company')} · {item.job_title}
        </strong>
        <span className="flex-shrink-0 font-mono text-xs text-neutral-500">{item.status}</span>
      </div>
      <div className="text-sm text-neutral-600">
        {item.department} · {item.salary_range}
      </div>
      <div className="text-xs text-neutral-400">
        {t('updated_at', { date: new Date(item.last_active_at).toLocaleDateString() })}
      </div>
    </Link>
  )
}
