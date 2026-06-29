'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateInvestment, type InvestmentActionType } from '@/hooks/useInvestments'
import { useBranches } from '@/hooks/useResumeBranches'
import { ACTION_ICON, ACTIONS } from './actionIcons'

export function NewInvestmentDialog({
  appId,
  onClose,
}: {
  appId: string
  onClose: () => void
}) {
  const t = useTranslations('investments')
  const create = useCreateInvestment(appId)
  const { data: branches } = useBranches(appId)
  const [action, setAction] = useState<InvestmentActionType>('submitted')
  const [when, setWhen] = useState(new Date().toISOString().slice(0, 16))
  const [channel, setChannel] = useState('')
  const [notes, setNotes] = useState('')
  const [branchId, setBranchId] = useState('')

  async function save() {
    await create.mutateAsync({
      action_type: action,
      action_at: new Date(when).toISOString(),
      channel,
      notes,
      used_resume_branch_id: branchId || null,
    })
    onClose()
  }

  const channelOptions = t('channel_options').split(',')

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md space-y-3 border border-fg bg-bg p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('new')}</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {ACTIONS.map((a) => {
            const Icon = ACTION_ICON[a]
            return (
              <button
                key={a}
                onClick={() => setAction(a)}
                className={`inline-flex items-center gap-1 border px-2 py-1 ${
                  action === a ? 'border-fg bg-fg text-fg-inverse' : 'border-border'
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {t(`action_${a}`)}
              </button>
            )
          })}
        </div>
        <input
          type="datetime-local"
          value={when}
          onChange={(e) => setWhen(e.target.value)}
          className="w-full border border-fg px-3 py-2"
        />
        <div>
          <label className="mb-1 block text-xs">{t('channel')}</label>
          <input
            list="ch-options"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full border border-border px-3 py-2"
          />
          <datalist id="ch-options">
            {channelOptions.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>
        <div>
          <label className="mb-1 block text-xs">{t('used_branch')}</label>
          <select
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            className="w-full border border-border px-3 py-2"
          >
            <option value="">—</option>
            {(branches ?? []).map((b) => (
              <option key={b.id} value={b.id}>
                {b.version_label}
                {b.match_score != null ? ` · ${b.match_score}` : ''}
              </option>
            ))}
          </select>
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('notes')}
          rows={2}
          className="w-full border border-border px-3 py-2"
        />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-bg-muted">
            {t('cancel')}
          </button>
          <button
            onClick={save}
            disabled={create.isPending}
            className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse hover:opacity-90 disabled:opacity-40"
          >
            {create.isPending ? '…' : t('save')}
          </button>
        </div>
      </div>
    </div>
  )
}
