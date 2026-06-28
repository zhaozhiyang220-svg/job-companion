'use client'
import { useState } from 'react'
import { X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDeleteCard, useUpdateCard } from '@/hooks/useMasterResume'
import type { AbilityCard } from './types'

export function AbilityCardItem({ card }: { card: AbilityCard }) {
  const t = useTranslations('master_resume')
  const [name, setName] = useState(card.skill_name)
  const [lvl, setLvl] = useState(card.level)
  const update = useUpdateCard('ability')
  const del = useDeleteCard('ability')

  return (
    <div className="space-y-2 border border-neutral-200 p-3">
      <div className="flex items-center justify-between gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => update.mutate({ id: card.id, body: { skill_name: name } })}
          className="min-w-0 flex-1 bg-transparent font-semibold outline-none"
          aria-label="skill name"
        />
        <button
          onClick={() => del.mutate(card.id)}
          className="text-neutral-400 hover:text-red-600"
          aria-label={t('delete')}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-neutral-500">Lv</span>
        <input
          type="number"
          min={1}
          max={5}
          value={lvl}
          onChange={(e) => setLvl(parseInt(e.target.value, 10) || 1)}
          onBlur={() => update.mutate({ id: card.id, body: { level: lvl } })}
          className="w-12 border border-neutral-300 px-1"
          aria-label="level"
        />
        {card.is_weak && <span className="font-mono text-xs text-orange-600">{t('weak_marker')}</span>}
      </div>
    </div>
  )
}
