'use client'
import { useTranslations } from 'next-intl'

export default function InvestmentsTab() {
  const t = useTranslations('opportunities')
  return <p className="text-sm text-neutral-600">{t('investments_tab_wip')}</p>
}
