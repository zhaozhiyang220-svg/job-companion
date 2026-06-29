import type { ReactNode } from 'react'
import { notFound } from 'next/navigation'
import { Inter, JetBrains_Mono, Noto_Sans_SC } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { locales, type Locale } from '@/i18n/request'
import { PostHogBoot } from '@/components/PostHogBoot'
import { Providers } from '@/lib/queryClient'

// Swiss Modernism 字体：Inter（英文/数字）、Noto Sans SC（中文）、JetBrains Mono（数字/代码）
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800', '900'],
  variable: '--font-sans',
  display: 'swap',
})
const notoSC = Noto_Sans_SC({
  subsets: ['latin'],
  weight: ['400', '500', '700', '900'],
  variable: '--font-sans-cn',
  display: 'swap',
})
const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
})

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }))
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  if (!locales.includes(locale as Locale)) notFound()
  const messages = await getMessages()
  return (
    <html
      lang={locale}
      className={`${inter.variable} ${notoSC.variable} ${jetbrains.variable}`}
    >
      <body className="bg-bg text-fg antialiased">
        <NextIntlClientProvider messages={messages}>
          <PostHogBoot />
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
