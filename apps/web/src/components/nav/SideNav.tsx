'use client'
import Link from 'next/link'
import { useParams, usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { BarChart3, BookOpen, Briefcase, FileText, MessageSquareQuote } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const ITEMS: { key: string; href: string; Icon: LucideIcon }[] = [
  { key: 'opportunities', href: 'opportunities', Icon: Briefcase },
  { key: 'master_resume', href: 'master-resume', Icon: FileText },
  { key: 'resources', href: 'resources', Icon: BookOpen },
  { key: 'weekly', href: 'weekly', Icon: BarChart3 },
  { key: 'coach', href: 'coach', Icon: MessageSquareQuote },
]

export function SideNav() {
  const t = useTranslations('nav')
  const { locale } = useParams<{ locale: string }>()
  const path = usePathname()
  return (
    <nav className="flex w-64 flex-col gap-0.5 border-r border-fg bg-bg-subtle p-4">
      <Link
        href={`/${locale}/dashboard`}
        className="mb-6 flex items-center gap-2 px-2 font-semibold tracking-tight"
      >
        <span className="mono flex h-7 w-7 items-center justify-center bg-fg text-sm text-fg-inverse">
          JC
        </span>
        <span>job/companion</span>
      </Link>
      {ITEMS.map(({ key, href, Icon }) => {
        const full = `/${locale}/${href}`
        const active = path === full || path.startsWith(`${full}/`)
        return (
          <Link
            key={key}
            href={full}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'flex items-center gap-3 border-l-2 px-3 py-2 text-sm transition-colors',
              active
                ? 'border-accent bg-bg-muted font-medium text-fg'
                : 'border-transparent text-fg-muted hover:bg-bg-subtle hover:text-fg',
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {t(key)}
          </Link>
        )
      })}
    </nav>
  )
}
