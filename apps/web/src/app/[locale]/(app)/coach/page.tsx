'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCoachAvailability } from '@/hooks/useCoach'
import { CoachInquiryDrawer } from '@/components/coach/CoachInquiryDrawer'

export default function CoachPage() {
  const t = useTranslations('coach')
  const { data: av } = useCoachAvailability()
  const [open, setOpen] = useState(false)
  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="heading">{t('title')}</h1>
      <p>{t('intro')}</p>
      <p className="text-xl font-mono">{t('price')}</p>
      {av &&
        (av.available ? (
          <p className="text-success">
            {t('slots_open', { n: av.slots_total - av.slots_taken })}
          </p>
        ) : (
          <p className="text-destructive">{t('slots_full')}</p>
        ))}
      <button
        onClick={() => setOpen(true)}
        className="h-12 border border-fg bg-fg px-6 text-fg-inverse hover:opacity-90"
      >
        {t('submit')}
      </button>
      {open && <CoachInquiryDrawer source="coach_page" onClose={() => setOpen(false)} />}
    </div>
  )
}
