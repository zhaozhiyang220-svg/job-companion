'use client'
import { useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { BarChart3 } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Events } from '@jc/shared-types'
import { track } from '@/lib/posthog'
import type { SuggestedAction } from '@/hooks/useWeekly'

export function ObservationCard({
  text,
  actions,
}: {
  text: string
  actions: SuggestedAction[]
}) {
  const t = useTranslations('weekly')
  const { locale } = useParams<{ locale: string }>()

  useEffect(() => {
    track(Events.WEEKLY_OPENED)
  }, [])

  if (!text) return null
  return (
    <div className="border border-black p-4">
      <h3 className="flex items-center gap-2 text-sm font-bold">
        <BarChart3 className="h-4 w-4" aria-hidden="true" />
        {t('observation')}
      </h3>
      <p className="mt-2 text-base leading-relaxed">{text}</p>
      {actions.length > 0 && (
        <>
          <h4 className="mt-3 text-xs text-neutral-500">{t('actions')}</h4>
          <div className="mt-1 flex flex-wrap gap-2">
            {actions.map((a, i) =>
              a.url ? (
                <Link
                  key={i}
                  href={a.url.startsWith('/') ? `/${locale}${a.url}` : a.url}
                  onClick={() => track(Events.WEEKLY_ACTION_CLICKED, { label: a.label })}
                  className="border border-black px-3 py-1 text-sm hover:bg-neutral-100"
                >
                  {a.label}
                </Link>
              ) : (
                <span key={i} className="border border-neutral-300 px-3 py-1 text-sm">
                  {a.label}
                </span>
              ),
            )}
          </div>
        </>
      )}
    </div>
  )
}
