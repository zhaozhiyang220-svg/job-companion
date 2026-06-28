'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'

export type InvestmentActionType =
  | 'submitted'
  | 'viewed'
  | 'interview_scheduled'
  | 'offer_received'
  | 'rejected'

export type Investment = {
  id: string
  action_type: InvestmentActionType
  action_at: string
  channel: string
  notes: string
  used_resume_branch_id: string | null
  used_branch_label: string | null
}

export type CreateInvestmentBody = {
  action_type: InvestmentActionType
  action_at: string
  channel?: string
  notes?: string
  used_resume_branch_id?: string | null
}

export function useInvestments(appId: string) {
  return useQuery({
    queryKey: ['investments', appId],
    queryFn: () => api<Investment[]>(`/api/v1/applications/${appId}/investments`),
    enabled: Boolean(appId),
  })
}

export function useCreateInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateInvestmentBody) =>
      api(`/api/v1/applications/${appId}/investments`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      track(Events.INVESTMENT_CREATED, { appId })
      qc.invalidateQueries({ queryKey: ['investments', appId] })
    },
  })
}

export function useUpdateInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { id: string; body: Partial<CreateInvestmentBody> }) =>
      api(`/api/v1/applications/${appId}/investments/${vars.id}`, {
        method: 'PATCH',
        body: JSON.stringify(vars.body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['investments', appId] }),
  })
}

export function useDeleteInvestment(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      api(`/api/v1/applications/${appId}/investments/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      track(Events.INVESTMENT_DELETED, { appId })
      qc.invalidateQueries({ queryKey: ['investments', appId] })
    },
  })
}
