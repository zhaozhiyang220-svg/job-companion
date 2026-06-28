'use client'
import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

const PERSONAS = ['fresh_grad', 'job_hopper', 'career_changer'] as const
type Persona = (typeof PERSONAS)[number]

export function PersonaPicker() {
  const t = useTranslations('onboarding')
  const { locale } = useParams<{ locale: string }>()
  const router = useRouter()
  const [pick, setPick] = useState<Persona | null>(null)
  const [busy, setBusy] = useState(false)

  async function save() {
    if (!pick) return
    setBusy(true)
    try {
      await api('/api/v1/me', { method: 'PATCH', body: JSON.stringify({ persona_type: pick }) })
      router.replace(`/${locale}/dashboard`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="w-96 space-y-3">
      {PERSONAS.map((p) => (
        <button
          key={p}
          onClick={() => setPick(p)}
          className={`w-full border p-3 text-left transition-colors ${
            pick === p ? 'border-black bg-black text-white' : 'border-neutral-300 hover:border-black'
          }`}
        >
          {t(p)}
        </button>
      ))}
      <button
        disabled={!pick || busy}
        onClick={save}
        className="h-10 w-full border border-black bg-black text-white transition-colors hover:bg-neutral-800 disabled:opacity-40"
      >
        {busy ? '…' : t('continue')}
      </button>
    </div>
  )
}
