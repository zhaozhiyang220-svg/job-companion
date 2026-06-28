import type { NextConfig } from 'next'
import createNextIntlPlugin from 'next-intl/plugin'
import { withSentryConfig } from '@sentry/nextjs'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@jc/shared-types'],
}

export default withSentryConfig(withNextIntl(nextConfig), {
  silent: true,
  // sentry org/project 在 CI 注入；本地无需上传 source map
})
