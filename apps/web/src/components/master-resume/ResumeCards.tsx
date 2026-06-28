'use client'
import type { ReactNode } from 'react'
import { Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useCreateCard, useDiagnose } from '@/hooks/useMasterResume'
import { AbilityCardItem } from './AbilityCardItem'
import { ProjectCardItem } from './ProjectCardItem'
import { ExperienceCardItem } from './ExperienceCardItem'
import type { MasterResumeData } from './types'

export function ResumeCards({ data }: { data: MasterResumeData }) {
  const t = useTranslations('master_resume')
  const addA = useCreateCard('ability')
  const addP = useCreateCard('project')
  const addE = useCreateCard('experience')
  const diag = useDiagnose()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => diag.mutate()}
          disabled={diag.isPending}
          className="h-10 border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800 disabled:opacity-40"
        >
          {diag.isPending ? t('diagnosing') : t('diagnose')}
        </button>
        {data.quality_score !== null && (
          <span className="font-mono text-sm">{t('score', { score: data.quality_score })}</span>
        )}
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Col title={t('ability')} onAdd={() => addA.mutate({ skill_name: t('new_ability'), level: 3 })}>
          {data.ability_cards.map((c) => (
            <AbilityCardItem key={c.id} card={c} />
          ))}
        </Col>
        <Col title={t('project')} onAdd={() => addP.mutate({ project_name: t('new_project') })}>
          {data.project_cards.map((c) => (
            <ProjectCardItem key={c.id} card={c} />
          ))}
        </Col>
        <Col
          title={t('experience')}
          onAdd={() => addE.mutate({ company: t('new_company'), title: '', is_current: false })}
        >
          {data.experience_cards.map((c) => (
            <ExperienceCardItem key={c.id} card={c} />
          ))}
        </Col>
      </div>
    </div>
  )
}

function Col({ title, onAdd, children }: { title: string; onAdd: () => void; children: ReactNode }) {
  const t = useTranslations('common')
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-black pb-1">
        <h2 className="font-bold">{title}</h2>
        <button onClick={onAdd} className="text-neutral-500 hover:text-black" aria-label={t('add')}>
          <Plus className="h-4 w-4" />
        </button>
      </div>
      {children}
    </div>
  )
}
