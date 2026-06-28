import { useTranslations } from 'next-intl'
import { PersonaPicker } from '@/components/auth/PersonaPicker'

export default function OnboardingPage() {
  const t = useTranslations('onboarding')
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="text-2xl font-bold tracking-tight">{t('question')}</h1>
      <PersonaPicker />
    </main>
  )
}
