'use client'
import Link from 'next/link'
import { useParams, usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { BarChart3, BookOpen, Briefcase, FileText, MessageSquareQuote } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

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
    <nav className="flex w-64 flex-col gap-1 border-r border-black bg-neutral-50 p-4">
      <div className="mb-6 flex items-center gap-2 px-2">
        <span className="flex h-7 w-7 items-center justify-center bg-black font-mono text-sm text-white">
          JC
        </span>
        <span className="font-bold tracking-tight">job/companion</span>
      </div>
      {ITEMS.map(({ key, href, Icon }) => {
        const full = `/${locale}/${href}`
        const active = path === full
        return (
          <Link
            key={key}
            href={full}
            className={`flex items-center gap-3 px-3 py-2 text-sm transition-colors ${
              active ? 'bg-black text-white' : 'hover:bg-neutral-200'
            }`}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {t(key)}
          </Link>
        )
      })}
    </nav>
  )
}
