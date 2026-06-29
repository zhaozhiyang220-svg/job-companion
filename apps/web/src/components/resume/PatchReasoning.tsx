'use client'
import { useTranslations } from 'next-intl'
import type { Reasoning } from './types'

export function PatchReasoning({ reasoning }: { reasoning: Reasoning[] }) {
  const t = useTranslations('resume_tab')
  if (!reasoning?.length) return null
  return (
    <details open className="border border-border p-3">
      <summary className="cursor-pointer text-sm font-semibold">
        {t('reasoning_title', { count: reasoning.length })}
      </summary>
      <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
        {reasoning.map((r, i) => (
          <li key={i}>{r.reason}</li>
        ))}
      </ol>
    </details>
  )
}
