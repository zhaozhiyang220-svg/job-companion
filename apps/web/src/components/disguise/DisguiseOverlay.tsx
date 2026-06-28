'use client'
import { PomodoroTimer } from './PomodoroTimer'
import { TodoList } from './TodoList'

export function DisguiseOverlay() {
  return (
    <div className="fixed inset-0 z-[9999] bg-white">
      <header className="border-b border-neutral-200 p-4 text-center font-bold">
        TimeFlow · Focus &amp; Tasks
      </header>
      <main className="flex flex-col items-center justify-center gap-12 p-12 md:flex-row">
        <PomodoroTimer />
        <TodoList />
      </main>
    </div>
  )
}
