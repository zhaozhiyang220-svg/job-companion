'use client'
import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Check } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

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
    <div className="w-full max-w-md space-y-3">
      {PERSONAS.map((p) => {
        const on = pick === p
        return (
          <button
            key={p}
            onClick={() => setPick(p)}
            aria-pressed={on}
            className={cn(
              'flex w-full items-center justify-between border p-4 text-left transition-colors',
              on ? 'border-accent bg-accent-soft' : 'border-border hover:border-fg',
            )}
          >
            <span className="font-medium text-fg">{t(p)}</span>
            <span
              className={cn(
                'flex h-5 w-5 items-center justify-center border',
                on ? 'border-accent bg-accent text-accent-fg' : 'border-border',
              )}
            >
              {on && <Check className="h-3 w-3" aria-hidden="true" />}
            </span>
          </button>
        )
      })}
      <Button onClick={save} disabled={!pick || busy} size="lg" className="w-full">
        {busy ? '…' : t('continue')}
      </Button>
    </div>
  )
}
