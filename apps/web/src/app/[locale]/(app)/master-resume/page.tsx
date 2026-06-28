'use client'
import { useTranslations } from 'next-intl'
import { UploadDropzone } from '@/components/master-resume/UploadDropzone'
import { ResumeCards } from '@/components/master-resume/ResumeCards'
import type { MasterResumeData } from '@/components/master-resume/types'
import { useMasterResume } from '@/hooks/useMasterResume'

export default function MasterResumePage() {
  const t = useTranslations('master_resume')
  const { data, refetch } = useMasterResume()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
      {!data ? (
        <>
          <p className="text-sm text-neutral-600">{t('empty')}</p>
          <UploadDropzone onParsed={() => void refetch()} />
        </>
      ) : (
        <ResumeCards data={data as MasterResumeData} />
      )}
    </div>
  )
}
