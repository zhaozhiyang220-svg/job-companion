import { type InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

// Swiss Input：黑边、直角、黑色 focus ring（由全局 :focus-visible 提供）（§4.2）
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-12 w-full border border-fg bg-bg px-4 text-base text-fg',
        'placeholder:text-fg-subtle',
        'focus:outline-none',
        'disabled:cursor-not-allowed disabled:bg-bg-muted',
        'aria-[invalid=true]:border-destructive',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'
