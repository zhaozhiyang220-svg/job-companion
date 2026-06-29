'use client'
import { useState } from 'react'
import { Check } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useCoachAvailability, useCreateInquiry } from '@/hooks/useCoach'

export function CoachInquiryDrawer({
  appId,
  onClose,
  source = 'resume_workspace',
}: {
  appId?: string
  branchId?: string
  onClose: () => void
  source?: string
}) {
  const t = useTranslations('coach')
  const { data: av } = useCoachAvailability()
  const create = useCreateInquiry()
  const [contact, setContact] = useState('')
  const [notes, setNotes] = useState('')
  const [done, setDone] = useState(false)

  async function submit() {
    await create.mutateAsync({
      application_id: appId,
      source_screen: source,
      contact_method: contact,
      notes,
    })
    setDone(true)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md space-y-3 border border-fg bg-bg p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('title')}</h3>
        <p className="text-sm">
          {t('intro')} · <b>{t('price')}</b>
        </p>
        {av &&
          (av.available ? (
            <p className="text-xs text-success">
              {t('slots_open', { n: av.slots_total - av.slots_taken })}
            </p>
          ) : (
            <p className="text-xs text-destructive">{t('slots_full')}</p>
          ))}
        {!done && av?.available && (
          <>
            <input
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              placeholder={t('contact_label')}
              className="w-full border border-fg px-3 py-2"
            />
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t('notes_label')}
              rows={3}
              className="w-full border border-border px-3 py-2"
            />
            <button
              onClick={submit}
              disabled={!contact || create.isPending}
              className="h-10 w-full border border-fg bg-fg text-fg-inverse hover:opacity-90 disabled:opacity-40"
            >
              {create.isPending ? t('submitting') : t('submit')}
            </button>
          </>
        )}
        {done && (
          <div className="flex items-center gap-2 text-success">
            <Check className="h-4 w-4" aria-hidden="true" />
            {t('submitted')}
          </div>
        )}
        {!av?.available && (
          <a
            href="mailto:notify@example.com?subject=订阅Coach名额"
            className="block text-center text-sm underline"
          >
            {t('subscribe_next_week')}
          </a>
        )}
        <button
          onClick={onClose}
          className="h-10 w-full border border-border hover:bg-bg-muted"
        >
          {t('close')}
        </button>
      </div>
    </div>
  )
}
