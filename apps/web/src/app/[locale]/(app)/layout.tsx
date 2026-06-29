import type { ReactNode } from 'react'
import { SideNav } from '@/components/nav/SideNav'
import { LocaleSwitcher } from '@/components/nav/LocaleSwitcher'
import { DisguiseToggle } from '@/components/disguise/DisguiseToggle'
import { SessionBootstrap } from '@/components/auth/SessionBootstrap'

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <SessionBootstrap>
      <div className="flex min-h-screen">
        <SideNav />
        <div className="flex flex-1 flex-col">
          <header className="sticky top-0 z-40 flex h-14 items-center justify-end gap-3 border-b border-border bg-bg px-6">
            <DisguiseToggle />
            <LocaleSwitcher />
          </header>
          <main className="mx-auto w-full max-w-6xl flex-1 p-6 md:p-8">{children}</main>
        </div>
      </div>
    </SessionBootstrap>
  )
}
