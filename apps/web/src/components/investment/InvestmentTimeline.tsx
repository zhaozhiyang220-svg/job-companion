'use client'
import { X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDeleteInvestment, useInvestments } from '@/hooks/useInvestments'
import { ACTION_ICON } from './actionIcons'

export function InvestmentTimeline({ appId }: { appId: string }) {
  const t = useTranslations('investments')
  const { data } = useInvestments(appId)
  const del = useDeleteInvestment(appId)

  if (!data?.length) return <p className="text-sm text-neutral-500">{t('empty')}</p>

  return (
    <ol className="space-y-4 border-l-2 border-neutral-200 pl-4">
      {data.map((iv) => {
        const Icon = ACTION_ICON[iv.action_type]
        return (
          <li key={iv.id} className="relative">
            <span className="absolute -left-[1.55rem] top-0.5 flex h-5 w-5 items-center justify-center bg-black text-white">
              <Icon className="h-3 w-3" aria-hidden="true" />
            </span>
            <div className="flex items-center justify-between">
              <div>
                <strong>{t(`action_${iv.action_type}`)}</strong>
                <span className="ml-2 text-xs text-neutral-500">
                  {new Date(iv.action_at).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => {
                  if (confirm(t('delete_confirm'))) del.mutate(iv.id)
                }}
                className="text-neutral-400 hover:text-red-600"
                aria-label={t('delete_confirm')}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex items-center gap-2 text-sm text-neutral-700">
              {iv.channel && (
                <span>
                  {t('channel')}: {iv.channel}
                </span>
              )}
              {iv.used_branch_label && (
                <span className="bg-neutral-100 px-1.5 font-mono text-xs">
                  {iv.used_branch_label}
                </span>
              )}
            </div>
            {iv.notes && <p className="mt-1 text-sm text-neutral-600">{iv.notes}</p>}
          </li>
        )
      })}
    </ol>
  )
}
