'use client'
import { useState, type ReactNode } from 'react'
import { Menu, X } from 'lucide-react'
import { SideNav } from '@/components/nav/SideNav'
import { LocaleSwitcher } from '@/components/nav/LocaleSwitcher'
import { DisguiseToggle } from '@/components/disguise/DisguiseToggle'

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="flex min-h-screen">
      {/* 桌面侧栏 */}
      <SideNav className="hidden md:flex" />

      {/* 移动端抽屉 */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 h-full w-72 max-w-[80%]">
            <SideNav className="h-full" onNavigate={() => setOpen(false)} />
            <button
              onClick={() => setOpen(false)}
              aria-label="close"
              className="absolute right-2 top-2 p-2 text-fg-muted hover:text-fg"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-bg px-4 md:px-6">
          <button
            onClick={() => setOpen(true)}
            aria-label="menu"
            className="-ml-1 p-2 text-fg md:hidden"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <div className="flex-1" />
          <DisguiseToggle />
          <LocaleSwitcher />
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  )
}
