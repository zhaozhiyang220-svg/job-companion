'use client'
import { useState } from 'react'
import { FileText, MessageSquare, RotateCcw } from 'lucide-react'
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
  const [replacing, setReplacing] = useState(false)

  // 重新解析成功后：拉取新数据并退出替换态，回到卡片视图（新简历会覆盖旧的）
  const finish = () => {
    void refetch()
    setReplacing(false)
    setMode('choose')
  }

  // 已有主简历且不在替换流程：展示卡片 + 「重新上传」入口
  if (data && !replacing) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
          <button
            onClick={() => {
              setReplacing(true)
              setMode('choose')
            }}
            className="inline-flex items-center gap-1 border border-neutral-300 px-3 py-1.5 text-sm hover:border-black"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            {t('replace')}
          </button>
        </div>
        <ResumeCards data={data as MasterResumeData} />
      </div>
    )
  }

  // 首次创建，或正在替换：上传 / 对话式录入
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight">{t('title')}</h1>
        {Boolean(data) && (
          <button
            onClick={() => {
              setReplacing(false)
              setMode('choose')
            }}
            className="border border-neutral-300 px-3 py-1.5 text-sm hover:border-black"
          >
            {t('cancel_replace')}
          </button>
        )}
      </div>
      {replacing && (
        <p className="text-sm text-neutral-500">{t('replace_hint')}</p>
      )}
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
      {mode === 'upload' && <UploadDropzone onParsed={finish} />}
      {mode === 'intake' && <IntakeDialog onDone={finish} />}
    </div>
  )
}
