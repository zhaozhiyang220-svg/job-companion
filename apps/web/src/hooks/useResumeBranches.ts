'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'
import type { BranchDetail, BranchSummary } from '@/components/resume/types'

const key = (appId: string, branchId?: string) =>
  branchId ? ['branches', appId, branchId] : ['branches', appId]

export function useBranches(appId: string) {
  return useQuery({
    queryKey: key(appId),
    queryFn: () => api<BranchSummary[]>(`/api/v1/applications/${appId}/branches`),
    enabled: Boolean(appId),
  })
}

export function useBranch(appId: string, branchId: string) {
  return useQuery({
    queryKey: key(appId, branchId),
    queryFn: () => api<BranchDetail>(`/api/v1/applications/${appId}/branches/${branchId}`),
    enabled: Boolean(branchId),
  })
}

export function useGenerateBranch(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { language?: string }) =>
      api<BranchDetail>(`/api/v1/applications/${appId}/branches`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (b) => {
      track(Events.RESUME_BRANCH_GENERATED, { match_score: b.match_score, lang: b.language })
      qc.invalidateQueries({ queryKey: ['branches', appId] })
    },
  })
}

export function useUpdateBranch(appId: string, branchId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { patch: Record<string, unknown>[] }) =>
      api<BranchDetail>(`/api/v1/applications/${appId}/branches/${branchId}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useRollback(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { branchId: string; prevId: string }) =>
      api<BranchDetail>(
        `/api/v1/applications/${appId}/branches/${vars.branchId}/rollback-to/${vars.prevId}`,
        { method: 'POST' },
      ),
    onSuccess: () => {
      track(Events.RESUME_BRANCH_ROLLBACK)
      qc.invalidateQueries({ queryKey: ['branches', appId] })
    },
  })
}

export function useDeleteBranch(appId: string, branchId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api(`/api/v1/applications/${appId}/branches/${branchId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['branches', appId] }),
  })
}

export function useExportBranch(appId: string, branchId: string) {
  return useMutation({
    mutationFn: (body: { language?: string; mask_current_company?: boolean }) =>
      api<{ pdf_url: string }>(
        `/api/v1/applications/${appId}/branches/${branchId}/export`,
        { method: 'POST', body: JSON.stringify(body) },
      ),
    onSuccess: (_r, vars) =>
      track(Events.RESUME_BRANCH_EXPORTED, {
        lang: vars.language,
        masked: vars.mask_current_company,
      }),
  })
}
