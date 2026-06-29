import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function Home() {
  const t = useTranslations('home')
  const tAuth = useTranslations('auth')
  const locale = useLocale()
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col px-6 md:px-8">
      {/* 顶栏 */}
      <header className="flex h-16 items-center justify-between">
        <div className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="mono flex h-7 w-7 items-center justify-center bg-fg text-sm text-fg-inverse">
            JC
          </span>
          <span>job/companion</span>
        </div>
        <Link href={`/${locale}/login`} className="text-sm font-medium text-fg-muted hover:text-fg">
          {tAuth('login')}
        </Link>
      </header>

      {/* Hero */}
      <div className="flex flex-1 flex-col justify-center py-20">
        <div className="section-label mb-6">01 — Job Companion</div>
        <h1 className="display-xl max-w-3xl text-fg">{t('title')}</h1>
        <p className="mt-6 max-w-xl text-lg leading-relaxed text-fg-muted">{t('tagline')}</p>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link href={`/${locale}/onboarding`}>
            <Button variant="accent" size="lg">
              {t('start')}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </Link>
          <Link href={`/${locale}/login`}>
            <Button variant="secondary" size="lg">
              {tAuth('login')}
            </Button>
          </Link>
        </div>
      </div>

      <footer className="border-t border-border py-6 text-sm text-fg-subtle">
        © {new Date().getFullYear()} Job Companion
      </footer>
    </main>
  )
}
