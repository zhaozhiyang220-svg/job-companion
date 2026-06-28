'use client'
import { use, useState } from 'react'
import { Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { InvestmentTimeline } from '@/components/investment/InvestmentTimeline'
import { NewInvestmentDialog } from '@/components/investment/NewInvestmentDialog'

export default function InvestmentsTab({ params }: { params: Promise<{ id: string }> }) {
  const { id: appId } = use(params)
  const t = useTranslations('investments')
  const [open, setOpen] = useState(false)
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight">{t('title')}</h2>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex h-10 items-center gap-2 border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t('new')}
        </button>
      </div>
      <InvestmentTimeline appId={appId} />
      {open && <NewInvestmentDialog appId={appId} onClose={() => setOpen(false)} />}
    </div>
  )
}
