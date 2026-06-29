import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { ArrowRight, Briefcase, FileText } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { SectionLabel } from '@/components/ui/section-label'

export default function DashboardPage() {
  const t = useTranslations('common')
  const tn = useTranslations('nav')
  const locale = useLocale()
  const quick = [
    { href: 'master-resume', Icon: FileText, label: tn('master_resume') },
    { href: 'opportunities', Icon: Briefcase, label: tn('opportunities') },
  ]
  return (
    <div className="space-y-8">
      <div>
        <SectionLabel num="01">Dashboard</SectionLabel>
        <h1 className="heading mt-2 text-fg">Dashboard</h1>
        <p className="mt-1 text-sm text-fg-muted">{t('module_wip')}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {quick.map(({ href, Icon, label }) => (
          <Link key={href} href={`/${locale}/${href}`}>
            <Card hover className="flex items-center justify-between">
              <span className="flex items-center gap-3 font-medium text-fg">
                <Icon className="h-5 w-5" aria-hidden="true" />
                {label}
              </span>
              <ArrowRight className="h-4 w-4 text-fg-subtle" aria-hidden="true" />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
