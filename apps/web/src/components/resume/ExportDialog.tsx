'use client'
import { useState } from 'react'
import { Download } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useExportBranch } from '@/hooks/useResumeBranches'

export function ExportDialog({
  appId,
  branchId,
  defaultLang,
  onClose,
}: {
  appId: string
  branchId: string
  defaultLang: string
  onClose: () => void
}) {
  const t = useTranslations('resume_tab')
  const exp = useExportBranch(appId, branchId)
  const [lang, setLang] = useState(defaultLang)
  const [mask, setMask] = useState(true)
  const [url, setUrl] = useState<string | null>(null)

  async function go() {
    const r = await exp.mutateAsync({ language: lang, mask_current_company: mask })
    setUrl(r.pdf_url)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-96 border border-fg bg-bg p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('export_title')}</h3>
        <div className="mt-3 space-y-3 text-sm">
          <div>
            <label className="mb-1 block">{t('export_language')}</label>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="w-full border border-fg px-2 py-1"
            >
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <label className="flex items-start gap-2">
            <input
              type="checkbox"
              checked={mask}
              onChange={(e) => setMask(e.target.checked)}
              className="mt-1"
            />
            <span>
              <b>{t('export_mask')}</b>
              <br />
              <span className="text-xs text-fg-subtle">{t('export_mask_hint')}</span>
            </span>
          </label>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="flex h-10 items-center justify-center gap-1 border border-fg bg-fg text-fg-inverse"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              {t('export_download')}
            </a>
          )}
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-bg-muted">
            {t('close')}
          </button>
          <button
            onClick={go}
            disabled={exp.isPending}
            className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse hover:opacity-90 disabled:opacity-40"
          >
            {exp.isPending ? t('export_doing') : url ? t('export_again') : t('export_go')}
          </button>
        </div>
      </div>
    </div>
  )
}
