import { useTranslations } from 'next-intl'

export default function ResourcesPage() {
  const t = useTranslations()
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-bold tracking-tight">{t('nav.resources')}</h1>
      <p className="text-sm text-neutral-600">{t('common.module_wip')}</p>
    </div>
  )
}
