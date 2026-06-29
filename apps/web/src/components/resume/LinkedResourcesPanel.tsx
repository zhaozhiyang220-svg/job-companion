'use client'
import { useState } from 'react'
import { Bookmark, Plus } from 'lucide-react'
import { useTranslations } from 'next-intl'
import {
  useApplicationResources,
  useLinkResourceToApp,
  useResources,
} from '@/hooks/useResources'

export function LinkedResourcesPanel({ appId }: { appId: string }) {
  const t = useTranslations('resources')
  const { data: linked } = useApplicationResources(appId)
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-3 border border-border p-3 text-sm">
      <div className="flex items-center justify-between">
        <strong>{t('linked_title')}</strong>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-1 border border-border px-2 py-0.5 text-xs hover:border-fg"
        >
          <Plus className="h-3 w-3" aria-hidden="true" />
          {t('link_btn')}
        </button>
      </div>
      <ul className="mt-2 space-y-1">
        {(linked ?? []).map((r) => (
          <li key={r.id} className="flex items-start gap-1">
            <Bookmark className="mt-0.5 h-3 w-3 flex-shrink-0" aria-hidden="true" />
            <span>
              {r.title}
              {r.ai_summary && (
                <span className="text-fg-subtle"> — {r.ai_summary.slice(0, 30)}…</span>
              )}
            </span>
          </li>
        ))}
        {linked?.length === 0 && <li className="text-fg-subtle">{t('linked_empty')}</li>}
      </ul>
      {open && <PickerDialog appId={appId} onClose={() => setOpen(false)} />}
    </div>
  )
}

function PickerDialog({ appId, onClose }: { appId: string; onClose: () => void }) {
  const t = useTranslations('resources')
  const { data } = useResources({})
  const link = useLinkResourceToApp(appId)
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="max-h-[70vh] w-96 overflow-auto border border-fg bg-bg p-4 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h4 className="mb-2 font-bold">{t('picker_title')}</h4>
        <ul className="space-y-1 text-sm">
          {(data?.items ?? []).map((r) => (
            <li key={r.id}>
              <button
                onClick={() => {
                  link.mutate(r.id)
                  onClose()
                }}
                className="w-full px-2 py-1 text-left hover:bg-bg-muted"
              >
                {r.title}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
