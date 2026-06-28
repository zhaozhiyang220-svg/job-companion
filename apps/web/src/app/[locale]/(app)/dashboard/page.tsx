import { useTranslations } from 'next-intl'

export default function DashboardPage() {
  const t = useTranslations('common')
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
      <p className="text-sm text-neutral-600">{t('module_wip')}</p>
    </div>
  )
}
