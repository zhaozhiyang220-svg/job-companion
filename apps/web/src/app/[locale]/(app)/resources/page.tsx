'use client'
import { useState } from 'react'
import { Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useResources, type ResourceType } from '@/hooks/useResources'
import { CollectionSidebar } from '@/components/resources/CollectionSidebar'
import { ResourceCard } from '@/components/resources/ResourceCard'
import { NewResourceDialog } from '@/components/resources/NewResourceDialog'

const TYPE_FILTERS: { v: ResourceType | undefined; label: string }[] = [
  { v: undefined, label: 'type_all' },
  { v: 'interview_recall', label: 'type_interview_recall' },
  { v: 'company_intel', label: 'type_company_intel' },
  { v: 'recruiter_bg', label: 'type_recruiter_bg' },
  { v: 'industry_doc', label: 'type_industry_doc' },
  { v: 'other', label: 'type_other' },
]

export default function ResourcesPage() {
  const t = useTranslations('resources')
  const [cid, setCid] = useState<string | null>(null)
  const [type, setType] = useState<ResourceType | undefined>(undefined)
  const [open, setOpen] = useState(false)
  const { data } = useResources({ type, collection_id: cid ?? undefined })

  return (
    <div className="flex gap-6">
      <CollectionSidebar currentId={cid} onPick={setCid} />
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
          <button
            onClick={() => setOpen(true)}
            className="inline-flex h-10 items-center gap-2 border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            {t('new_resource')}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => setType(f.v)}
              className={`border px-3 py-1 text-sm ${
                type === f.v ? 'border-black bg-black text-white' : 'border-neutral-300'
              }`}
            >
              {t(f.label)}
            </button>
          ))}
        </div>
        <div className="space-y-3">
          {(data?.items ?? []).map((r) => (
            <ResourceCard key={r.id} r={r} />
          ))}
          {data?.items.length === 0 && <p className="text-sm text-neutral-500">{t('empty')}</p>}
        </div>
      </div>
      {open && <NewResourceDialog onClose={() => setOpen(false)} />}
    </div>
  )
}
