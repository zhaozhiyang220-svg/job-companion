'use client'
import { useTranslations } from 'next-intl'

export function CoachInquiryDrawer({ onClose }: { onClose: () => void }) {
  const t = useTranslations('resume_tab')
  // v1 极简：展示说明 + 微信号；Plan 7 接 /api/v1/coach/inquiries 表单
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-96 border border-black bg-white p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('coach_title')}</h3>
        <p className="mt-2 text-sm">{t('coach_desc')}</p>
        <p className="mt-1 text-xs text-neutral-500">{t('coach_slots')}</p>
        <div className="mt-4 text-sm">{t('coach_contact')}</div>
        <button
          onClick={onClose}
          className="mt-4 h-10 w-full border border-black bg-black text-white hover:bg-neutral-800"
        >
          {t('coach_close')}
        </button>
      </div>
    </div>
  )
}
