import { useTranslations } from 'next-intl'
import { MagicLinkForm } from '@/components/auth/MagicLinkForm'
import { WeChatQR } from '@/components/auth/WeChatQR'

export default function LoginPage() {
  const t = useTranslations('auth')
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8">
      <h1 className="text-2xl font-bold tracking-tight">{t('login')}</h1>
      <MagicLinkForm />
      <hr className="w-72 border-neutral-200" />
      <WeChatQR />
    </main>
  )
}
