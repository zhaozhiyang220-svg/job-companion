'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateApplication } from '@/hooks/useApplications'
import { CapacityGate } from '@/components/common/CapacityGate'

export function NewOpportunityDialog({ onClose }: { onClose: () => void }) {
  const t = useTranslations('opportunities')
  const [text, setText] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [gateCode, setGateCode] = useState<string | null>(null)
  const create = useCreateApplication()

  async function submit() {
    setErr(null)
    try {
      await create.mutateAsync({ raw_text: text })
      onClose()
    } catch (e) {
      const m = String(e).match(/capacity_(active|monthly)/)
      if (m) setGateCode(`capacity_${m[1]}`)
      else setErr(String(e))
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl border border-fg bg-bg p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-3 font-bold">{t('new')}</h3>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          placeholder={t('paste_jd')}
          className="w-full border border-fg p-2 text-sm"
        />
        {err && (
          <p role="alert" className="mt-2 text-sm text-destructive">
            {err}
          </p>
        )}
        <div className="mt-3 flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-bg-muted">
            {t('cancel')}
          </button>
          <button
            onClick={submit}
            disabled={create.isPending || !text.trim()}
            className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse hover:opacity-90 disabled:opacity-40"
          >
            {create.isPending ? t('parsing') : t('submit')}
          </button>
        </div>
      </div>
      {gateCode && <CapacityGate code={gateCode} onClose={() => setGateCode(null)} />}
    </div>
  )
}
