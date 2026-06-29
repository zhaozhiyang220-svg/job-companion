'use client'
import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { StatCards } from '@/components/internal/StatCards'
import { SimpleChart } from '@/components/internal/SimpleChart'
import type { DailyRow, DashboardSummary } from '@/components/internal/types'

const KEY = 'jc_internal_pwd'
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

function Dashboard() {
  const sp = useSearchParams()
  const [pwd, setPwd] = useState('')
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [series, setSeries] = useState<DailyRow[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const q = sp.get('password')
    const stored = typeof window !== 'undefined' ? sessionStorage.getItem(KEY) : null
    setPwd(q ?? stored ?? '')
  }, [sp])

  useEffect(() => {
    if (!pwd) return
    sessionStorage.setItem(KEY, pwd)
    const headers = { 'X-Internal-Password': pwd }
    Promise.all([
      fetch(`${BASE}/internal/dashboard/summary`, { headers }).then((r) =>
        r.ok ? (r.json() as Promise<DashboardSummary>) : Promise.reject(new Error(String(r.status))),
      ),
      fetch(`${BASE}/internal/dashboard/timeseries?days=30`, { headers }).then((r) =>
        r.ok
          ? (r.json() as Promise<{ daily: DailyRow[] }>)
          : Promise.reject(new Error(String(r.status))),
      ),
    ])
      .then(([s, t]) => {
        setSummary(s)
        setSeries(t.daily)
      })
      .catch((e) => setErr(String(e)))
  }, [pwd])

  if (!pwd) {
    return (
      <main className="p-8">
        <input
          type="password"
          placeholder="internal password"
          onBlur={(e) => setPwd(e.target.value)}
          className="border border-fg px-3 py-2"
        />
      </main>
    )
  }
  if (err) return <main className="p-8 text-destructive">{err}</main>
  if (!summary) return <main className="p-8">Loading…</main>

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6">
      <h1 className="heading">Internal Dashboard</h1>
      <StatCards s={summary} />
      <SimpleChart data={series} valueKey="dau" label="DAU" />
      <SimpleChart data={series} valueKey="ai_calls" label="AI calls / day" />
      <SimpleChart data={series} valueKey="ai_cost" label="AI cost (USD) / day" />
    </main>
  )
}

export default function InternalDashboardPage() {
  return (
    <Suspense fallback={<main className="p-8">Loading…</main>}>
      <Dashboard />
    </Suspense>
  )
}
