'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

export default function VerifyPage() {
  const params = useSearchParams()
  const router = useRouter()
  const { locale } = useParams<{ locale: string }>()
  const t = useTranslations('auth')
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const token = params.get('token')
    if (!token) {
      setErr(t('missing_token'))
      return
    }
    api('/api/v1/auth/magic-link/verify', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
      .then(async () => {
        const me = await api<{ persona_type: string | null }>('/api/v1/me')
        router.replace(me.persona_type ? `/${locale}/dashboard` : `/${locale}/onboarding`)
      })
      .catch((e) => setErr(String(e)))
  }, [params, router, locale, t])

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      {err ? (
        <p role="alert" className="text-sm text-red-600">
          {err}
        </p>
      ) : (
        <p className="text-sm text-neutral-600">{t('verifying')}</p>
      )}
    </main>
  )
}
