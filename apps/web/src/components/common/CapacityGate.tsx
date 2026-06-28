'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { CoachInquiryDrawer } from '@/components/coach/CoachInquiryDrawer'

const MSG_KEY: Record<string, string> = {
  capacity_active: 'gate_capacity_active',
  capacity_monthly: 'gate_capacity_monthly',
  capacity_resources: 'gate_capacity_resources',
  capacity_collections: 'gate_capacity_collections',
}

export function CapacityGate({ code, onClose }: { code: string; onClose: () => void }) {
  const t = useTranslations('opportunities')
  const [openCoach, setOpenCoach] = useState(false)

  if (openCoach) {
    return (
      <CoachInquiryDrawer
        source="capacity_gate"
        onClose={() => {
          setOpenCoach(false)
          onClose()
        }}
      />
    )
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-96 border border-black bg-white p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('gate_title')}</h3>
        <p className="mt-2 text-sm text-neutral-700">{t(MSG_KEY[code] ?? 'gate_capacity_active')}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-neutral-100">
            {t('gate_close')}
          </button>
          <button
            onClick={() => setOpenCoach(true)}
            className="h-10 border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800"
          >
            {t('gate_find_coach')}
          </button>
        </div>
      </div>
    </div>
  )
}
