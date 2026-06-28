'use client'
import { useParams, usePathname, useRouter } from 'next/navigation'

export function LocaleSwitcher() {
  const { locale } = useParams<{ locale: string }>()
  const router = useRouter()
  const path = usePathname()
  const other = locale === 'zh' ? 'en' : 'zh'
  return (
    <button
      onClick={() => router.push(path.replace(`/${locale}`, `/${other}`))}
      className="h-8 border border-neutral-300 px-2 text-sm hover:border-black"
      aria-label={`Switch to ${other}`}
    >
      {locale === 'zh' ? 'EN' : '中'}
    </button>
  )
}
