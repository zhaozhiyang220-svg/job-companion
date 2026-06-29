'use client'
import { Eye, EyeOff } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDisguise } from '@/hooks/useDisguise'
import { DisguiseOverlay } from './DisguiseOverlay'

export function DisguiseToggle() {
  const { on, toggle } = useDisguise()
  const t = useTranslations('common')
  return (
    <>
      <button
        onClick={toggle}
        className="inline-flex h-8 items-center gap-1 border border-border px-2 text-sm hover:border-fg"
        title="Ctrl+`"
        aria-label={t('disguise')}
      >
        {on ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        <span>{t('disguise')}</span>
      </button>
      {on && <DisguiseOverlay />}
    </>
  )
}
