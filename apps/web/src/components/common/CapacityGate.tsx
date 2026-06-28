'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'

export function CapacityGate({ code, onClose }: { code: string; onClose: () => void }) {
  const t = useTranslations('opportunities')
  const { locale } = useParams<{ locale: string }>()
  const message =
    code === 'capacity_active'
      ? t('gate_capacity_active')
      : code === 'capacity_monthly'
        ? t('gate_capacity_monthly')
        : t('gate_capacity_active')

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-96 border border-black bg-white p-6 shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold">{t('gate_title')}</h3>
        <p className="mt-2 text-sm text-neutral-700">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="h-10 px-3 text-sm hover:bg-neutral-100">
            {t('gate_close')}
          </button>
          <Link
            href={`/${locale}/coach`}
            onClick={onClose}
            className="flex h-10 items-center border border-black bg-black px-4 text-sm text-white hover:bg-neutral-800"
          >
            {t('gate_find_coach')}
          </Link>
        </div>
      </div>
    </div>
  )
}
