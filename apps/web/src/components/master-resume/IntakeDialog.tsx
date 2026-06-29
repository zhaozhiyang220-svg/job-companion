'use client'
import { useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { useIntakeAnswer, useIntakeFinalize, useIntakeStart } from '@/hooks/useIntake'

type Turn = { role: 'q' | 'a'; text: string }

export function IntakeDialog({ onDone }: { onDone: () => void }) {
  const t = useTranslations('master_resume')
  const start = useIntakeStart()
  const answer = useIntakeAnswer()
  const finalize = useIntakeFinalize()
  const [sid, setSid] = useState<string | null>(null)
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [done, setDone] = useState(false)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    start.mutateAsync().then((r) => {
      setSid(r.session_id)
      setTurns([{ role: 'q', text: r.first_question }])
    })
  }, [start])

  async function send() {
    if (!sid || !input.trim()) return
    const ans = input
    setTurns((prev) => [...prev, { role: 'a', text: ans }])
    setInput('')
    const r = await answer.mutateAsync({ session_id: sid, answer: ans })
    if (r.done) setDone(true)
    else if (r.next_question) setTurns((prev) => [...prev, { role: 'q', text: r.next_question! }])
  }

  async function finish() {
    if (!sid) return
    await finalize.mutateAsync({ session_id: sid })
    onDone()
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="h-96 space-y-2 overflow-auto border border-border p-4">
        {turns.map((turn, i) => (
          <div key={i} className={turn.role === 'q' ? '' : 'text-right'}>
            <span
              className={`inline-block px-3 py-2 text-sm ${
                turn.role === 'q' ? 'bg-bg-muted' : 'bg-fg text-fg-inverse'
              }`}
            >
              {turn.text}
            </span>
          </div>
        ))}
      </div>
      {!done ? (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void send()
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('intake_input_placeholder')}
            className="h-10 flex-1 border border-fg px-3"
          />
          <button
            type="submit"
            disabled={answer.isPending}
            className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse disabled:opacity-40"
          >
            {t('intake_send')}
          </button>
        </form>
      ) : (
        <button
          onClick={finish}
          disabled={finalize.isPending}
          className="h-12 w-full border border-fg bg-fg text-fg-inverse disabled:opacity-40"
        >
          {finalize.isPending ? t('intake_generating') : t('intake_finish')}
        </button>
      )}
    </div>
  )
}
