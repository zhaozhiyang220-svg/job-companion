import { Bookmark, Building2, Mic, Newspaper, UserCircle2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ResourceType } from '@/hooks/useResources'

export const RESOURCE_ICON: Record<ResourceType, LucideIcon> = {
  interview_recall: Mic,
  company_intel: Building2,
  recruiter_bg: UserCircle2,
  industry_doc: Newspaper,
  other: Bookmark,
}
