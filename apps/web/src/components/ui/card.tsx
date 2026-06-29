import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

// Swiss Card：无圆角、无阴影，只用边框；可选 hover 边框变黑（§4.3）
export function Card({
  className,
  hover = false,
  ...props
}: HTMLAttributes<HTMLDivElement> & { hover?: boolean }) {
  return (
    <div
      className={cn(
        'border border-border bg-bg p-6',
        hover && 'transition-colors duration-200 hover:border-fg',
        className,
      )}
      {...props}
    />
  )
}
