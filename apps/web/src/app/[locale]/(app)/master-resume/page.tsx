'use client'
import { useState } from 'react'
import { FileText, MessageSquare } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { UploadDropzone } from '@/components/master-resume/UploadDropzone'
import { IntakeDialog } from '@/components/master-resume/IntakeDialog'
import { ResumeCards } from '@/components/master-resume/ResumeCards'
import type { MasterResumeData } from '@/components/master-resume/types'
import { useMasterResume } from '@/hooks/useMasterResume'

type Mode = 'choose' | 'upload' | 'intake'

export default function MasterResumePage() {
  const t = useTranslations('master_resume')
  const { data, refetch } = useMasterResume()
  const [mode, setMode] = useState<Mode>('choose')

  if (data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
        <ResumeCards data={data as MasterResumeData} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
      {mode === 'choose' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <button
            onClick={() => setMode('upload')}
            className="flex flex-col items-center gap-3 border border-neutral-300 p-8 hover:border-black"
          >
            <FileText className="h-8 w-8" aria-hidden="true" />
            {t('choose_upload')}
          </button>
          <button
            onClick={() => setMode('intake')}
            className="flex flex-col items-center gap-3 border border-neutral-300 p-8 hover:border-black"
          >
            <MessageSquare className="h-8 w-8" aria-hidden="true" />
            {t('choose_intake')}
          </button>
        </div>
      )}
      {mode === 'upload' && <UploadDropzone onParsed={() => void refetch()} />}
      {mode === 'intake' && <IntakeDialog onDone={() => void refetch()} />}
    </div>
  )
}
