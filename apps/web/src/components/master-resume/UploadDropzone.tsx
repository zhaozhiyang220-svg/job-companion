'use client'
import { useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Upload } from 'lucide-react'
import { Events } from '@jc/shared-types'
import { useParseResume, useUploadInit } from '@/hooks/useMasterResume'
import { track } from '@/lib/posthog'

type Stage = 'idle' | 'uploading' | 'parsing' | 'error'

export function UploadDropzone({ onParsed }: { onParsed: () => void }) {
  const t = useTranslations('master_resume')
  const init = useUploadInit()
  const parse = useParseResume()
  const inp = useRef<HTMLInputElement>(null)
  const [stage, setStage] = useState<Stage>('idle')
  const [progress, setProgress] = useState(0)
  const [err, setErr] = useState<string | null>(null)

  async function handle(file: File) {
    setErr(null)
    setStage('uploading')
    setProgress(0)
    track(Events.MASTER_RESUME_UPLOAD_STARTED)
    try {
      const { upload_url, s3_key } = await init.mutateAsync({
        filename: file.name,
        content_type: file.type,
      })
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('PUT', upload_url)
        xhr.setRequestHeader('Content-Type', file.type)
        xhr.upload.onprogress = (e) =>
          e.lengthComputable && setProgress(Math.round((e.loaded / e.total) * 100))
        xhr.onload = () =>
          xhr.status < 300 ? resolve() : reject(new Error(`upload ${xhr.status}`))
        xhr.onerror = () => reject(new Error('network'))
        xhr.send(file)
      })
      setStage('parsing')
      await parse.mutateAsync({ s3_key })
      setStage('idle')
      onParsed()
    } catch (e) {
      setErr(String(e))
      setStage('error')
    }
  }

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault()
        const f = e.dataTransfer.files?.[0]
        if (f) void handle(f)
      }}
      onClick={() => inp.current?.click()}
      className="flex cursor-pointer flex-col items-center gap-3 border-2 border-dashed border-border p-12 text-center hover:border-fg"
    >
      <input
        ref={inp}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) void handle(f)
        }}
      />
      <Upload className="h-8 w-8 text-fg-subtle" aria-hidden="true" />
      {stage === 'idle' && <p className="text-sm">{t('drop_or_click')}</p>}
      {stage === 'uploading' && (
        <p className="text-sm">
          {t('uploading')} {progress}%
        </p>
      )}
      {stage === 'parsing' && <p className="text-sm">{t('parsing')}</p>}
      {stage === 'error' && (
        <p role="alert" className="text-sm text-destructive">
          {err}
        </p>
      )}
    </div>
  )
}
