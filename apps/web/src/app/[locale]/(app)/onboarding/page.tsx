import { useTranslations } from 'next-intl'
import { PersonaPicker } from '@/components/auth/PersonaPicker'

export default function OnboardingPage() {
  const t = useTranslations('onboarding')
  return (
    <main className="flex min-h-[70vh] flex-col items-center justify-center gap-8">
      <h1 className="display-md text-center text-fg">{t('question')}</h1>
      <PersonaPicker />
    </main>
  )
}
