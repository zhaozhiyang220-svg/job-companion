'use client'
import type { ReactNode } from 'react'
import { Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useCreateCard, useDiagnose } from '@/hooks/useMasterResume'
import { AbilityCardItem } from './AbilityCardItem'
import { ProjectCardItem } from './ProjectCardItem'
import { ExperienceCardItem } from './ExperienceCardItem'
import { DiagnosisReportView } from './DiagnosisReportView'
import type { MasterResumeData } from './types'

export function ResumeCards({
  data,
  onRebuild,
}: {
  data: MasterResumeData
  onRebuild?: () => void
}) {
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
          className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse hover:opacity-90 disabled:opacity-40"
        >
          {diag.isPending ? t('diagnosing') : t('diagnose')}
        </button>
        {data.quality_score !== null && !diag.data && (
          <span className="font-mono text-sm">{t('score', { score: data.quality_score })}</span>
        )}
      </div>
      {diag.isError && (
        <p role="alert" className="text-sm text-destructive">
          {t('diagnose_failed')}
        </p>
      )}
      {diag.data && (
        <div className="border border-border p-5">
          <DiagnosisReportView report={diag.data} onRebuild={onRebuild} />
        </div>
      )}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Col title={t('ability')} onAdd={() => addA.mutate({ skill_name: t('new_ability'), level: 3 })}>
          {(data.ability_cards ?? []).map((c) => (
            <AbilityCardItem key={c.id} card={c} />
          ))}
        </Col>
        <Col title={t('project')} onAdd={() => addP.mutate({ project_name: t('new_project') })}>
          {(data.project_cards ?? []).map((c) => (
            <ProjectCardItem key={c.id} card={c} />
          ))}
        </Col>
        <Col
          title={t('experience')}
          onAdd={() => addE.mutate({ company: t('new_company'), title: '', is_current: false })}
        >
          {(data.experience_cards ?? []).map((c) => (
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
      <div className="flex items-center justify-between border-b border-fg pb-1">
        <h2 className="font-bold">{title}</h2>
        <button onClick={onAdd} className="text-fg-subtle hover:text-fg" aria-label={t('add')}>
          <Plus className="h-4 w-4" />
        </button>
      </div>
      {children}
    </div>
  )
}
