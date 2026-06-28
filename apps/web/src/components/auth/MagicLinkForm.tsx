'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

type State = 'idle' | 'sending' | 'sent' | 'error'

export function MagicLinkForm() {
  const t = useTranslations('auth')
  const [email, setEmail] = useState('')
  const [state, setState] = useState<State>('idle')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setState('sending')
    try {
      await api('/api/v1/auth/magic-link/request', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setState('sent')
    } catch {
      setState('error')
    }
  }

  return (
    <form onSubmit={submit} className="w-72 space-y-3">
      <label htmlFor="email" className="block text-sm font-medium">
        {t('email_label')}
      </label>
      <input
        id="email"
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="h-12 w-full border border-black px-4 text-base focus:outline-none focus:ring-2 focus:ring-black"
      />
      <button
        type="submit"
        disabled={state === 'sending'}
        className="h-10 w-full border border-black bg-black text-white transition-colors hover:bg-neutral-800 disabled:opacity-40"
      >
        {t('send_magic_link')}
      </button>
      {state === 'sent' && (
        <p role="status" className="text-sm text-green-600">
          {t('link_sent')}
        </p>
      )}
      {state === 'error' && (
        <p role="alert" className="text-sm text-red-600">
          {t('send_failed')}
        </p>
      )}
    </form>
  )
}
