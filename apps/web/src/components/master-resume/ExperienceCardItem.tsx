'use client'
import { useState } from 'react'
import { X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDeleteCard, useUpdateCard } from '@/hooks/useMasterResume'
import { CurrentCompanyWarning } from './CurrentCompanyWarning'
import type { ExperienceCard } from './types'

export function ExperienceCardItem({ card }: { card: ExperienceCard }) {
  const t = useTranslations('master_resume')
  const [c, setC] = useState({
    company: card.company,
    title: card.title,
    period: card.period,
    scope: card.scope,
  })
  const update = useUpdateCard('experience')
  const del = useDeleteCard('experience')
  const save = () => update.mutate({ id: card.id, body: c })

  return (
    <div className="space-y-2 border border-neutral-200 p-3">
      {card.is_current && <CurrentCompanyWarning />}
      <div className="flex items-center justify-between gap-2">
        <input
          value={c.company}
          onChange={(e) => setC({ ...c, company: e.target.value })}
          onBlur={save}
          className="min-w-0 flex-1 bg-transparent font-semibold outline-none"
          aria-label="company"
        />
        <button
          onClick={() => del.mutate(card.id)}
          className="text-neutral-400 hover:text-red-600"
          aria-label={t('delete')}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <input
        value={c.title}
        onChange={(e) => setC({ ...c, title: e.target.value })}
        onBlur={save}
        placeholder={t('title_field')}
        className="w-full border-b border-neutral-200 bg-transparent text-sm"
      />
      <input
        value={c.period}
        onChange={(e) => setC({ ...c, period: e.target.value })}
        onBlur={save}
        placeholder={t('period_field')}
        className="w-full border-b border-neutral-200 bg-transparent text-xs"
      />
      <textarea
        value={c.scope}
        onChange={(e) => setC({ ...c, scope: e.target.value })}
        onBlur={save}
        placeholder={t('scope_field')}
        className="w-full border border-neutral-300 p-1 text-sm"
        rows={2}
      />
    </div>
  )
}
