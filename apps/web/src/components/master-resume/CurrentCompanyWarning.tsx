'use client'
import { Lock } from 'lucide-react'
import { useTranslations } from 'next-intl'

export function CurrentCompanyWarning() {
  const t = useTranslations('master_resume')
  return (
    <div className="flex items-center gap-2 border border-accent bg-accent-soft px-2 py-1 text-xs text-fg">
      <Lock className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      {t('current_company_warning')}
    </div>
  )
}
