'use client'
import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

export function WeChatQR() {
  const t = useTranslations('auth')
  const [qrUrl, setQrUrl] = useState<string | null>(null)

  useEffect(() => {
    api<{ qr_url: string }>('/api/v1/auth/wechat/qr')
      .then((d) => setQrUrl(d.qr_url))
      .catch(() => setQrUrl(null))
  }, [])

  if (!qrUrl) return <p className="text-sm text-fg-muted">{t('wechat_scan')}…</p>
  return (
    <a
      href={qrUrl}
      target="_blank"
      rel="noreferrer"
      className="inline-block border border-fg px-4 py-3 text-sm hover:bg-bg-subtle"
    >
      {t('wechat_scan')}
    </a>
  )
}
