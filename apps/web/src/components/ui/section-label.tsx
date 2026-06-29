import { cn } from '@/lib/utils'

// §NN — Title 章节编号（Swiss 特色，§2.2）。num 如 "01"，children 是标题文案。
export function SectionLabel({
  num,
  children,
  className,
}: {
  num: string
  children?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('section-label', className)}>
      {num}
      {children && <span className="ml-2 normal-case tracking-normal text-fg-muted">— {children}</span>}
    </div>
  )
}
