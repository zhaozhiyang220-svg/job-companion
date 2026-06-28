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
    const b = await gen.mutateAsync({})
    onGenerated(b.id)
  }

  return (
    <button
      onClick={go}
      disabled={gen.isPending}
      className={`border border-black bg-black text-white hover:bg-neutral-800 disabled:opacity-40 ${
        isFirst ? 'w-full py-6 text-lg' : 'h-10 px-4 text-sm'
      }`}
    >
      {gen.isPending ? t('generating') : isFirst ? t('generate_first') : t('generate_next')}
    </button>
  )
}
