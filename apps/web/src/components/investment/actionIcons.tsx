import { CalendarClock, Eye, PartyPopper, Send, XCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { InvestmentActionType } from '@/hooks/useInvestments'

export const ACTION_ICON: Record<InvestmentActionType, LucideIcon> = {
  submitted: Send,
  viewed: Eye,
  interview_scheduled: CalendarClock,
  offer_received: PartyPopper,
  rejected: XCircle,
}

export const ACTIONS: InvestmentActionType[] = [
  'submitted',
  'viewed',
  'interview_scheduled',
  'offer_received',
  'rejected',
]
