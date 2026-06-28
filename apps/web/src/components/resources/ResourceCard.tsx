'use client'
import { Building2, X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDeleteResource, type Resource } from '@/hooks/useResources'
import { RESOURCE_ICON } from './resourceIcons'

export function ResourceCard({ r }: { r: Resource }) {
  const t = useTranslations('resources')
  const del = useDeleteResource()
  const Icon = RESOURCE_ICON[r.type] ?? RESOURCE_ICON.other

  return (
    <div className="space-y-1 border border-neutral-200 p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-semibold">
          <Icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          {r.title}
        </div>
        <button
          onClick={() => {
            if (confirm(t('delete_confirm'))) del.mutate(r.id)
          }}
          className="text-neutral-400 hover:text-red-600"
          aria-label={t('delete_confirm')}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      {r.ai_summary && <p className="text-sm text-neutral-700">{r.ai_summary}</p>}
      {r.linked_company_names.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-neutral-600">
          <Building2 className="h-3 w-3" aria-hidden="true" />
          {r.linked_company_names.join(', ')}
        </div>
      )}
      {r.ai_extracted_signals.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer">
            {t('signals')} ({r.ai_extracted_signals.length})
          </summary>
          <ul className="list-disc pl-4">
            {r.ai_extracted_signals.map((s, i) => (
              <li key={i}>
                <b>{s.type}：</b>
                {s.content}
              </li>
            ))}
          </ul>
        </details>
      )}
      {r.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {r.tags.map((g) => (
            <span key={g} className="bg-neutral-100 px-2 py-0.5 text-xs">
              {g}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
