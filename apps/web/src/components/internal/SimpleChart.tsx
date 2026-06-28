'use client'
import type { DailyRow } from './types'

export function SimpleChart({
  data,
  valueKey,
  label,
}: {
  data: DailyRow[]
  valueKey: 'dau' | 'ai_calls' | 'ai_cost'
  label: string
}) {
  const values = data.map((d) => Number(d[valueKey]) || 0)
  const max = Math.max(1, ...values)
  const W = 600
  const H = 120
  const pad = 24
  const x = (i: number) => pad + (i / Math.max(1, data.length - 1)) * (W - 2 * pad)
  const y = (v: number) => H - pad - (v / max) * (H - 2 * pad)
  const pts = data.map((d, i) => `${x(i)},${y(Number(d[valueKey]) || 0)}`).join(' ')
  return (
    <div className="border border-neutral-200 p-3">
      <div className="mb-1 text-xs text-neutral-500">
        {label} · max {max.toFixed(2)}
      </div>
      <svg width={W} height={H} className="max-w-full">
        <polyline fill="none" stroke="#000" strokeWidth={2} points={pts} />
        {data.map((d, i) => (
          <circle key={i} cx={x(i)} cy={y(Number(d[valueKey]) || 0)} r={2} fill="#000" />
        ))}
      </svg>
    </div>
  )
}
