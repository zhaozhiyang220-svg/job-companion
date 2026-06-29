import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { MagicLinkForm } from '@/components/auth/MagicLinkForm'
import { WeChatQR } from '@/components/auth/WeChatQR'

export default function LoginPage() {
  const t = useTranslations('auth')
  const locale = useLocale()
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <Link
        href={`/${locale}`}
        className="mb-8 flex items-center gap-2 font-semibold tracking-tight"
      >
        <span className="mono flex h-7 w-7 items-center justify-center bg-fg text-sm text-fg-inverse">
          JC
        </span>
        <span>job/companion</span>
      </Link>
      <Card className="w-full max-w-sm space-y-6 p-8">
        <h1 className="heading">{t('login')}</h1>
        <MagicLinkForm />
        <div className="flex items-center gap-3 text-xs text-fg-subtle">
          <span className="h-px flex-1 bg-border" />
          <span className="mono">OR</span>
          <span className="h-px flex-1 bg-border" />
        </div>
        <WeChatQR />
      </Card>
    </main>
  )
}
