import { type ComponentType, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

// 居中 + 虚线边框框定空白 + 大图标 + 标题 + 描述 + CTA（§4.10）
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ComponentType<{ className?: string; 'aria-hidden'?: boolean }>
  title: string
  description?: string
  action?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center border border-dashed border-border px-6 py-16 text-center',
        className,
      )}
    >
      {Icon && <Icon className="mb-4 h-10 w-10 text-fg-subtle" aria-hidden={true} />}
      <h3 className="subheading text-fg">{title}</h3>
      {description && <p className="mt-2 max-w-sm text-sm text-fg-muted">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
