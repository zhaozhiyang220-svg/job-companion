'use client'
import Link from 'next/link'
import { useParams, usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { BarChart3, Briefcase, Lock, Send, Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

type Tab = {
  key: string
  labelKey: string
  Icon: LucideIcon
  enabled: boolean
  soonKey?: string
}

const TABS: Tab[] = [
  { key: 'resume', labelKey: 'tab_resume', Icon: Sparkles, enabled: true },
  { key: 'investments', labelKey: 'tab_investments', Icon: Send, enabled: true },
  { key: 'interview', labelKey: 'tab_interview', Icon: Briefcase, enabled: false, soonKey: 'soon_interview' },
  { key: 'recap', labelKey: 'tab_recap', Icon: BarChart3, enabled: false, soonKey: 'soon_recap' },
  { key: 'offer', labelKey: 'tab_offer', Icon: Briefcase, enabled: false, soonKey: 'soon_offer' },
]

export function OpportunityTabs({ appId }: { appId: string }) {
  const t = useTranslations('opportunities')
  const { locale } = useParams<{ locale: string }>()
  const path = usePathname()

  return (
    <nav className="flex gap-1 border-b border-border">
      {TABS.map((tab) => {
        const href = `/${locale}/opportunities/${appId}/${tab.key}`
        const active = path === href
        if (!tab.enabled) {
          return (
            <span
              key={tab.key}
              title={tab.soonKey ? t(tab.soonKey) : undefined}
              className="inline-flex cursor-not-allowed items-center gap-1 px-3 pb-2 text-sm text-fg-subtle"
            >
              <tab.Icon className="h-4 w-4" aria-hidden="true" />
              {t(tab.labelKey)}
              <Lock className="h-3 w-3" aria-hidden="true" />
            </span>
          )
        }
        return (
          <Link
            key={tab.key}
            href={href}
            className={`-mb-px inline-flex items-center gap-1 border-b-2 px-3 pb-2 text-sm ${
              active ? 'border-fg font-bold' : 'border-transparent text-fg-muted hover:text-fg'
            }`}
          >
            <tab.Icon className="h-4 w-4" aria-hidden="true" />
            {t(tab.labelKey)}
          </Link>
        )
      })}
    </nav>
  )
}
