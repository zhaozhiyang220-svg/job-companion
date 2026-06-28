'use client'
import { useState } from 'react'
import { Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useApplications, type ApplicationStatus } from '@/hooks/useApplications'
import { OpportunityCard } from '@/components/opportunities/OpportunityCard'
import { NewOpportunityDialog } from '@/components/opportunities/NewOpportunityDialog'

export default function OpportunitiesPage() {
  const t = useTranslations('opportunities')
  const [tab, setTab] = useState<ApplicationStatus | undefined>(undefined)
  const [open, setOpen] = useState(false)
  const { data } = useApplications(tab)

  const tabs: { v: ApplicationStatus | undefined; label: string }[] = [
    { v: undefined, label: t('tab_all') },
    { v: 'drafting', label: t('tab_drafting') },
    { v: 'archived', label: t('tab_archived') },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex h-10 items-center gap-2 border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t('new')}
        </button>
      </div>
      <div className="flex gap-3 border-b border-neutral-200">
        {tabs.map((x) => (
          <button
            key={x.label}
            onClick={() => setTab(x.v)}
            className={`-mb-px border-b-2 pb-2 text-sm ${
              tab === x.v ? 'border-black font-bold' : 'border-transparent text-neutral-500'
            }`}
          >
            {x.label}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {(data?.items ?? []).map((it) => (
          <OpportunityCard key={it.id} item={it} />
        ))}
        {data?.items.length === 0 && <p className="text-sm text-neutral-500">{t('empty')}</p>}
      </div>
      {open && <NewOpportunityDialog onClose={() => setOpen(false)} />}
    </div>
  )
}
