'use client'
import { useState } from 'react'
import { MessageSquareQuote } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Events } from '@jc/shared-types'
import { track } from '@/lib/posthog'
import { CoachInquiryDrawer } from './CoachInquiryDrawer'

export function CoachInquiryButton({
  appId,
  branchId,
}: {
  appId: string
  branchId?: string
}) {
  const t = useTranslations('resume_tab')
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        onClick={() => {
          track(Events.COACH_INQUIRY_OPENED, { appId, branchId, source: 'resume_workspace' })
          setOpen(true)
        }}
        className="inline-flex h-8 items-center gap-1 border border-[--color-accent] px-3 text-sm text-[--color-accent] hover:bg-accent-soft"
      >
        <MessageSquareQuote className="h-4 w-4" aria-hidden="true" />
        {t('coach_btn')}
      </button>
      {open && (
        <CoachInquiryDrawer
          appId={appId}
          branchId={branchId}
          source="resume_workspace"
          onClose={() => setOpen(false)}
        />
      )}
    </>
  )
}
