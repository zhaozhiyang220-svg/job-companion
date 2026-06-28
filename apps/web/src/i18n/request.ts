import { getRequestConfig } from 'next-intl/server'
import { notFound } from 'next/navigation'

export const locales = ['zh', 'en'] as const
export type Locale = (typeof locales)[number]
export const defaultLocale: Locale = 'zh'

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale
  const locale =
    requested && locales.includes(requested as Locale) ? (requested as Locale) : undefined
  if (!locale) notFound()
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  }
})
