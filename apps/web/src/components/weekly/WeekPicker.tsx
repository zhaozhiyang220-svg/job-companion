'use client'
import { useTranslations } from 'next-intl'
import { useWeeklyHistory } from '@/hooks/useWeekly'

export function WeekPicker({
  value,
  onChange,
}: {
  value: string | undefined
  onChange: (v: string | undefined) => void
}) {
  const t = useTranslations('weekly')
  const { data } = useWeeklyHistory(12)
  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value || undefined)}
      className="border border-neutral-300 px-3 py-1 text-sm"
    >
      <option value="">{t('this_week')}</option>
      {(data ?? []).map((h) => (
        <option key={h.week_of} value={h.week_of}>
          {h.week_of}
        </option>
      ))}
    </select>
  )
}
