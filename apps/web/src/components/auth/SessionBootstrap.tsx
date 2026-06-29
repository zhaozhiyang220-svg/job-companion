'use client'
import { useEffect, useState, type ReactNode } from 'react'
import { api } from '@/lib/api'

// 免登录访客：进入 app 时若无会话，自动建一个匿名访客 session，
// 这样受保护接口（建岗位、传简历等）无需用户先登录即可使用。
export function SessionBootstrap({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        await api('/api/v1/me')
      } catch {
        try {
          await api('/api/v1/auth/guest', { method: 'POST' })
        } catch {
          // 静默失败：后续接口若仍 401 会各自提示
        }
      }
      if (!cancelled) setReady(true)
    })()
    return () => {
      cancelled = true
    }
  }, [])
  if (!ready) return null
  return <>{children}</>
}
