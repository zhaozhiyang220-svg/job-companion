'use client'
import { useState } from 'react'

type Item = { id: number; text: string; done: boolean }

export function TodoList() {
  const [items, setItems] = useState<Item[]>([
    { id: 1, text: 'Reply emails', done: false },
    { id: 2, text: 'Write weekly report', done: false },
  ])
  const [val, setVal] = useState('')

  function add(e: React.FormEvent) {
    e.preventDefault()
    if (!val.trim()) return
    setItems((it) => [...it, { id: Date.now(), text: val.trim(), done: false }])
    setVal('')
  }

  function toggle(id: number) {
    setItems((it) => it.map((x) => (x.id === id ? { ...x, done: !x.done } : x)))
  }

  return (
    <div className="w-80 space-y-3">
      <form onSubmit={add}>
        <input
          value={val}
          onChange={(e) => setVal(e.target.value)}
          placeholder="Add task…"
          className="w-full border border-fg px-3 py-2"
          aria-label="Add task"
        />
      </form>
      <ul className="space-y-1">
        {items.map((i) => (
          <li key={i.id} className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={i.done}
              onChange={() => toggle(i.id)}
              aria-label={i.text}
            />
            <span className={i.done ? 'text-fg-subtle line-through' : ''}>{i.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
