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
          <header className="flex h-12 items-center justify-end gap-3 border-b border-black px-4">
            <DisguiseToggle />
            <LocaleSwitcher />
          </header>
          <main className="flex-1 p-8">{children}</main>
        </div>
      </div>
    </SessionBootstrap>
  )
}
