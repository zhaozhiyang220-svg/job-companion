'use client'
import { useEffect, useState } from 'react'

export function PomodoroTimer() {
  const [secs, setSecs] = useState(25 * 60)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setSecs((s) => Math.max(0, s - 1)), 1000)
    return () => clearInterval(id)
  }, [running])

  const m = String(Math.floor(secs / 60)).padStart(2, '0')
  const s = String(secs % 60).padStart(2, '0')

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="font-mono text-6xl tabular-nums">
        {m}:{s}
      </div>
      <div className="flex gap-2">
        <button onClick={() => setRunning((r) => !r)} className="border border-fg px-4 py-2">
          {running ? 'Pause' : 'Start'}
        </button>
        <button
          onClick={() => {
            setSecs(25 * 60)
            setRunning(false)
          }}
          className="border border-fg px-4 py-2"
        >
          Reset
        </button>
      </div>
    </div>
  )
}
