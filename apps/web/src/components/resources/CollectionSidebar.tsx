'use client'
import { useState } from 'react'
import { BookOpen, FolderOpen, X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import {
  useCollections,
  useCreateCollection,
  useDeleteCollection,
} from '@/hooks/useResources'

export function CollectionSidebar({
  currentId,
  onPick,
}: {
  currentId: string | null
  onPick: (id: string | null) => void
}) {
  const t = useTranslations('resources')
  const { data: cols } = useCollections()
  const create = useCreateCollection()
  const del = useDeleteCollection()
  const [newName, setNewName] = useState('')

  return (
    <aside className="w-56 flex-shrink-0 space-y-1 border-r border-border pr-3 text-sm">
      <button
        onClick={() => onPick(null)}
        className={`flex w-full items-center gap-2 px-2 py-1 text-left ${
          !currentId ? 'bg-fg text-fg-inverse' : 'hover:bg-bg-muted'
        }`}
      >
        <BookOpen className="h-4 w-4" aria-hidden="true" />
        {t('coll_all')}
      </button>
      {(cols ?? []).map((c) => (
        <div key={c.id} className="group flex items-center justify-between">
          <button
            onClick={() => onPick(c.id)}
            className={`flex flex-1 items-center gap-2 px-2 py-1 text-left ${
              currentId === c.id ? 'bg-fg text-fg-inverse' : 'hover:bg-bg-muted'
            }`}
          >
            <FolderOpen className="h-4 w-4" aria-hidden="true" />
            {c.name} <span className="text-xs opacity-60">({c.item_count})</span>
          </button>
          <button
            onClick={() => {
              if (confirm(t('delete_confirm'))) del.mutate(c.id)
            }}
            className="px-1 text-fg-subtle opacity-0 hover:text-destructive group-hover:opacity-100"
            aria-label={t('delete_confirm')}
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!newName.trim()) return
          create.mutate({ name: newName.trim() })
          setNewName('')
        }}
        className="border-t border-border pt-3"
      >
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder={t('new_collection')}
          className="w-full border border-border px-2 py-1 text-sm"
        />
      </form>
    </aside>
  )
}
