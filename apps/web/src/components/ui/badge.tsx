import { type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

// mono + 直角 + 1px 边（§4.7）。注意：var() 整色值不支持 /alpha，soft 用预设浅色。
const badge = cva(
  'mono inline-flex items-center gap-1 border px-2 py-0.5 text-xs leading-5',
  {
    variants: {
      variant: {
        default: 'border-border bg-bg-muted text-fg-muted',
        accent: 'border-accent bg-accent-soft text-accent',
        success: 'border-success bg-bg text-success',
        outline: 'border-fg bg-bg text-fg',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>) {
  return <span className={cn(badge({ variant }), className)} {...props} />
}
