import { useTranslations, useLocale } from 'next-intl'
import Link from 'next/link'

export default function Home() {
  const t = useTranslations('home')
  const tAuth = useTranslations('auth')
  const locale = useLocale()
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
      <p className="text-muted-foreground">{t('tagline')}</p>
      <Link
        href={`/${locale}/login`}
        className="rounded-md bg-black px-6 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-80"
      >
        {tAuth('login')}
      </Link>
    </main>
  )
}
