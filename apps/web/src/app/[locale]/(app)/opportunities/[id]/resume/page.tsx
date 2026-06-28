'use client'
import { useTranslations } from 'next-intl'

export default function ResumeTab() {
  const t = useTranslations('opportunities')
  return <p className="text-sm text-neutral-600">{t('resume_tab_wip')}</p>
}
