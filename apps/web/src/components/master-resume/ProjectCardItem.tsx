'use client'
import { useState } from 'react'
import { X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDeleteCard, useUpdateCard } from '@/hooks/useMasterResume'
import type { ProjectCard } from './types'

const STAR_KEYS = ['situation', 'task', 'action', 'result'] as const

export function ProjectCardItem({ card }: { card: ProjectCard }) {
  const t = useTranslations('master_resume')
  const [open, setOpen] = useState(false)
  const [star, setStar] = useState(
    card.star ?? { situation: '', task: '', action: '', result: '' },
  )
  const update = useUpdateCard('project')
  const del = useDeleteCard('project')

  return (
    <div className="space-y-2 border border-border p-3">
      <div className="flex items-center justify-between gap-2">
        <strong className="min-w-0 truncate">{card.project_name}</strong>
        <div className="flex flex-shrink-0 items-center gap-2">
          {card.is_weak && <span className="font-mono text-xs text-accent">{t('weak_marker')}</span>}
          <button onClick={() => setOpen((o) => !o)} className="text-xs underline">
            {open ? t('collapse') : t('edit')}
          </button>
          <button
            onClick={() => del.mutate(card.id)}
            className="text-fg-subtle hover:text-destructive"
            aria-label={t('delete')}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="text-xs text-fg-subtle">
        {card.role} · {card.period}
      </div>
      {card.is_weak && card.weak_reasons.length > 0 && (
        <ul className="list-disc pl-4 text-xs text-accent">
          {card.weak_reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}
      {open && (
        <div className="space-y-2 text-sm">
          {STAR_KEYS.map((k) => (
            <div key={k}>
              <label className="block text-xs uppercase tracking-wide text-fg-subtle">{k}</label>
              <textarea
                value={star[k]}
                onChange={(e) => setStar({ ...star, [k]: e.target.value })}
                onBlur={() => update.mutate({ id: card.id, body: { star } })}
                className="w-full border border-border p-1"
                rows={2}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
