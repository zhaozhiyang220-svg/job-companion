import { useTranslations } from 'next-intl'

export default function MasterResumePage() {
  const t = useTranslations()
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-bold tracking-tight">{t('nav.master_resume')}</h1>
      <p className="text-sm text-neutral-600">{t('common.module_wip')}</p>
    </div>
  )
}
