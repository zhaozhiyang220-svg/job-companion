'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useCreateResource, type ResourceType } from '@/hooks/useResources'

const TYPES: ResourceType[] = [
  'interview_recall',
  'company_intel',
  'recruiter_bg',
  'industry_doc',
  'other',
]

export function NewResourceDialog({ onClose }: { onClose: () => void }) {
  const t = useTranslations('resources')
  const create = useCreateResource()
  const [type, setType] = useState<ResourceType>('interview_recall')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [tags, setTags] = useState('')

  async function save() {
    await create.mutateAsync({
      type,
      title,
      content_text: content,
      source_url: url || undefined,
      tags: tags
        ? tags
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
        : [],
    })
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl space-y-3 border border-fg bg-bg p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('new_resource')}</h3>
        <div className="flex flex-wrap gap-2 text-sm">
          {TYPES.map((tp) => (
            <button
              key={tp}
              onClick={() => setType(tp)}
              className={`border px-2 py-1 ${
                tp === type ? 'border-fg bg-fg text-fg-inverse' : 'border-border'
              }`}
            >
              {t(`type_${tp}`)}
            </button>
          ))}
        </div>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={t('fields_title')}
          className="w-full border border-fg px-3 py-2"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={t('fields_content')}
          rows={8}
          className="w-full border border-fg px-3 py-2"
        />
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={t('fields_source_url')}
          className="w-full border border-border px-3 py-2 text-sm"
        />
        <input
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder={t('fields_tags')}
          className="w-full border border-border px-3 py-2 text-sm"
        />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-bg-muted">
            {t('cancel')}
          </button>
          <button
            onClick={save}
            disabled={create.isPending || !title.trim()}
            className="h-10 border border-fg bg-fg px-4 text-sm text-fg-inverse hover:opacity-90 disabled:opacity-40"
          >
            {create.isPending ? '…' : t('save')}
          </button>
        </div>
      </div>
    </div>
  )
}
