import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

// Swiss Modernism Button — 5 变体 × 4 尺寸（design/UI_UX_GUIDE.md §4.1）
const button = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium tracking-tight transition-[color,background-color,border-color,transform] duration-150 active:scale-[0.97] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        primary: 'border border-fg bg-fg text-fg-inverse hover:bg-neutral-800',
        secondary: 'border border-fg bg-bg text-fg hover:bg-bg-subtle',
        ghost: 'bg-transparent text-fg hover:bg-bg-muted',
        destructive: 'border border-destructive bg-destructive text-white hover:opacity-90',
        accent: 'border border-accent bg-accent text-accent-fg hover:bg-accent-hover',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-base',
        xl: 'h-14 px-8 text-lg',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = 'button', ...props }, ref) => (
    <button ref={ref} type={type} className={cn(button({ variant, size }), className)} {...props} />
  ),
)
Button.displayName = 'Button'

export { button as buttonVariants }
