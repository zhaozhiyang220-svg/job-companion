import type { ReactNode } from 'react'
import { AppShell } from '@/components/nav/AppShell'
import { SessionBootstrap } from '@/components/auth/SessionBootstrap'

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <SessionBootstrap>
      <AppShell>{children}</AppShell>
    </SessionBootstrap>
  )
}
