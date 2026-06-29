'use client'
import { use, useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { useApplication } from '@/hooks/useApplications'
import { useBranch, useBranches } from '@/hooks/useResumeBranches'
import { JDInsightPanel } from '@/components/resume/JDInsightPanel'
import { BranchSwitcher } from '@/components/resume/BranchSwitcher'
import { GenerateButton } from '@/components/resume/GenerateButton'
import { ResumeWorkspace } from '@/components/resume/ResumeWorkspace'

export default function ResumeTab({ params }: { params: Promise<{ id: string }> }) {
  const { id: appId } = use(params)
  const t = useTranslations('resume_tab')
  const { data: appData } = useApplication(appId)
  const { data: branches } = useBranches(appId)
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    if (branches?.length && !activeId) {
      const active = branches.find((b) => b.is_active) ?? branches[0]
      setActiveId(active.id)
    }
  }, [branches, activeId])

  const { data: branch } = useBranch(appId, activeId ?? '')

  return (
    <div className="flex min-h-[60vh] gap-6">
      <JDInsightPanel
        jp={appData?.job_posting}
        matchScore={branch?.match_score ?? null}
        appId={appId}
      />
      <section className="flex-1 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <BranchSwitcher appId={appId} currentId={activeId} onPick={setActiveId} />
          {branches && branches.length > 0 && (
            <GenerateButton appId={appId} isFirst={false} onGenerated={setActiveId} />
          )}
        </div>
        {!branches?.length ? (
          <div className="space-y-4">
            <p className="text-sm text-fg-subtle">{t('no_branch')}</p>
            <GenerateButton appId={appId} isFirst onGenerated={setActiveId} />
          </div>
        ) : (
          branch && <ResumeWorkspace appId={appId} branch={branch} />
        )}
      </section>
    </div>
  )
}
