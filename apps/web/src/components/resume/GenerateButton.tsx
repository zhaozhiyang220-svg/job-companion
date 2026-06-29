'use client'
import { useTranslations } from 'next-intl'
import { useGenerateBranch } from '@/hooks/useResumeBranches'

export function GenerateButton({
  appId,
  isFirst,
  onGenerated,
}: {
  appId: string
  isFirst: boolean
  onGenerated: (id: string) => void
}) {
  const t = useTranslations('resume_tab')
  const gen = useGenerateBranch(appId)

  async function go() {
    try {
      const b = await gen.mutateAsync({})
      onGenerated(b.id)
    } catch {
      // 失败（如未建主简历）由下方提示展示，避免未捕获异常
    }
  }

  const needMaster = gen.isError && String(gen.error).includes('master resume not found')

  return (
    <div className="space-y-2">
      <button
        onClick={go}
        disabled={gen.isPending}
        className={`border border-fg bg-fg text-fg-inverse hover:opacity-90 disabled:opacity-40 ${
          isFirst ? 'w-full py-6 text-lg' : 'h-10 px-4 text-sm'
        }`}
      >
        {gen.isPending ? t('generating') : isFirst ? t('generate_first') : t('generate_next')}
      </button>
      {gen.isError && (
        <p role="alert" className="text-sm text-destructive">
          {needMaster ? t('need_master') : t('generate_failed')}
        </p>
      )}
    </div>
  )
}
