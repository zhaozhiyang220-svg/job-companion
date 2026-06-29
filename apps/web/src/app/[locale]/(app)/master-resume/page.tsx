'use client'
import { useState } from 'react'
import { FileText, MessageSquare, RotateCcw } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { UploadDropzone } from '@/components/master-resume/UploadDropzone'
import { IntakeDialog } from '@/components/master-resume/IntakeDialog'
import { ResumeCards } from '@/components/master-resume/ResumeCards'
import type { MasterResumeData } from '@/components/master-resume/types'
import { useMasterResume } from '@/hooks/useMasterResume'
import { Button } from '@/components/ui/button'
import { SectionLabel } from '@/components/ui/section-label'

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

  const Header = ({ action }: { action?: React.ReactNode }) => (
    <div className="flex items-end justify-between gap-4">
      <div>
        <SectionLabel num="01">Master Resume</SectionLabel>
        <h1 className="heading mt-2 text-fg">{t('title')}</h1>
      </div>
      {action}
    </div>
  )

  // 已有主简历且不在替换流程：展示卡片 + 「重新上传」入口
  if (data && !replacing) {
    return (
      <div className="space-y-6">
        <Header
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setReplacing(true)
                setMode('choose')
              }}
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              {t('replace')}
            </Button>
          }
        />
        <ResumeCards data={data as MasterResumeData} />
      </div>
    )
  }

  // 首次创建，或正在替换：上传 / 对话式录入
  return (
    <div className="space-y-6">
      <Header
        action={
          Boolean(data) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setReplacing(false)
                setMode('choose')
              }}
            >
              {t('cancel_replace')}
            </Button>
          )
        }
      />
      {replacing && <p className="text-sm text-fg-muted">{t('replace_hint')}</p>}
      {mode === 'choose' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[
            { m: 'upload' as const, Icon: FileText, label: t('choose_upload') },
            { m: 'intake' as const, Icon: MessageSquare, label: t('choose_intake') },
          ].map(({ m, Icon, label }) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className="flex flex-col items-center gap-3 border border-border p-10 text-center transition-colors hover:border-fg hover:bg-bg-subtle"
            >
              <Icon className="h-8 w-8 text-fg" aria-hidden="true" />
              <span className="font-medium text-fg">{label}</span>
            </button>
          ))}
        </div>
      )}
      {mode === 'upload' && <UploadDropzone onParsed={finish} />}
      {mode === 'intake' && <IntakeDialog onDone={finish} />}
    </div>
  )
}
