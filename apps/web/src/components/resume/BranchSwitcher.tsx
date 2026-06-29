'use client'
import { useBranches } from '@/hooks/useResumeBranches'

export function BranchSwitcher({
  appId,
  currentId,
  onPick,
}: {
  appId: string
  currentId: string | null
  onPick: (id: string) => void
}) {
  const { data } = useBranches(appId)
  return (
    <div className="flex flex-wrap items-center gap-2">
      {(data ?? []).map((b) => (
        <button
          key={b.id}
          onClick={() => onPick(b.id)}
          className={`h-8 border px-3 font-mono text-sm ${
            b.id === currentId ? 'border-fg bg-fg text-fg-inverse' : 'border-border'
          }`}
        >
          {b.version_label}
          {b.match_score != null && ` · ${b.match_score}`}
        </button>
      ))}
    </div>
  )
}
