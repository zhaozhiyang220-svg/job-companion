'use client'
import { use, type ReactNode } from 'react'
import { useTranslations } from 'next-intl'
import { useApplication } from '@/hooks/useApplications'
import { OpportunityTabs } from '@/components/opportunities/OpportunityTabs'

export default function OppLayout({
  children,
  params,
}: {
  children: ReactNode
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const t = useTranslations('opportunities')
  const { data } = useApplication(id)
  const jp = data?.job_posting

  return (
    <div className="space-y-4">
      <header className="border-b border-neutral-200 pb-3">
        <h1 className="text-xl font-bold tracking-tight">
          {jp?.company_name || t('loading')}
          {jp?.job_title ? ` · ${jp.job_title}` : ''}
        </h1>
        <div className="text-sm text-neutral-500">
          {jp ? `${jp.department} · ${jp.salary_range}` : ''}
        </div>
      </header>
      <OpportunityTabs appId={id} />
      <main>{children}</main>
    </div>
  )
}
