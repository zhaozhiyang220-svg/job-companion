'use client'
import { useState, type ReactNode } from 'react'
import { Upload } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Events } from '@jc/shared-types'
import { track } from '@/lib/posthog'
import { CoachInquiryButton } from '@/components/coach/CoachInquiryButton'
import { DiffView } from './DiffView'
import { ExportDialog } from './ExportDialog'
import { PatchReasoning } from './PatchReasoning'
import { RenderedResume } from './RenderedResume'
import type { BranchDetail } from './types'

type Mode = 'diff' | 'side' | 'merge'

export function ResumeWorkspace({ appId, branch }: { appId: string; branch: BranchDetail }) {
  const t = useTranslations('resume_tab')
  const [mode, setMode] = useState<Mode>('side')
  const [exportOpen, setExportOpen] = useState(false)

  const modeLabel: Record<Mode, string> = {
    diff: t('mode_diff'),
    side: t('mode_side'),
    merge: t('mode_merge'),
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {(['diff', 'side', 'merge'] as Mode[]).map((m) => (
          <button
            key={m}
            onClick={() => {
              track(Events.RESUME_MODE_SWITCHED, { mode: m })
              setMode(m)
            }}
            className={`h-8 border px-3 text-sm ${
              mode === m ? 'border-fg bg-fg text-fg-inverse' : 'border-border'
            }`}
          >
            {modeLabel[m]}
          </button>
        ))}
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => setExportOpen(true)}
            className="inline-flex h-8 items-center gap-1 border border-fg bg-fg px-3 text-sm text-fg-inverse hover:opacity-90"
          >
            <Upload className="h-4 w-4" aria-hidden="true" />
            {t('export_pdf')}
          </button>
          <CoachInquiryButton appId={appId} branchId={branch.id} />
        </div>
      </div>

      {mode === 'side' ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Panel title={t('panel_master')}>
            <RenderedResume data={branch.master_snapshot} />
          </Panel>
          <Panel title={t('panel_patch', { label: branch.version_label })}>
            <DiffView rendered={branch.rendered_resume} />
          </Panel>
        </div>
      ) : mode === 'diff' ? (
        <Panel title={t('panel_patch_diff', { label: branch.version_label })}>
          <DiffView rendered={branch.rendered_resume} />
        </Panel>
      ) : (
        <Panel title={t('panel_merge')}>
          <RenderedResume data={branch.rendered_resume} />
        </Panel>
      )}

      <PatchReasoning reasoning={branch.ai_reasoning} />

      {exportOpen && (
        <ExportDialog
          appId={appId}
          branchId={branch.id}
          defaultLang={branch.language}
          onClose={() => setExportOpen(false)}
        />
      )}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="border border-border p-3">
      <h4 className="mb-2 text-sm font-bold">{title}</h4>
      {children}
    </div>
  )
}
