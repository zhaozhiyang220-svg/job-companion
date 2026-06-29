'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField } from '@/components/ui/form-field'

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
    <form onSubmit={submit} className="space-y-4">
      <FormField label={t('email_label')} htmlFor="email">
        <Input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
      </FormField>
      <Button type="submit" size="lg" className="w-full" disabled={state === 'sending'}>
        {state === 'sending' ? '…' : t('send_magic_link')}
      </Button>
      {state === 'sent' && (
        <p role="status" className="text-sm text-success">
          {t('link_sent')}
        </p>
      )}
      {state === 'error' && (
        <p role="alert" className="text-sm text-destructive">
          {t('send_failed')}
        </p>
      )}
    </form>
  )
}
