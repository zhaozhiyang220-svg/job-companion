'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'
import type { DiagnosisReport } from '@/components/master-resume/DiagnosisReportView'

type CardType = 'ability' | 'project' | 'experience'

export function useMasterResume() {
  return useQuery({
    queryKey: ['master-resume'],
    queryFn: () => api<unknown>('/api/v1/master-resume'),
  })
}

export function useUploadInit() {
  return useMutation({
    mutationFn: (vars: { filename: string; content_type: string }) =>
      api<{ upload_url: string; s3_key: string }>('/api/v1/master-resume/upload-init', {
        method: 'POST',
        body: JSON.stringify(vars),
      }),
  })
}

export function useParseResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { s3_key: string }) =>
      api('/api/v1/master-resume/parse', { method: 'POST', body: JSON.stringify(vars) }),
    onSuccess: () => {
      track(Events.MASTER_RESUME_PARSED)
      qc.invalidateQueries({ queryKey: ['master-resume'] })
    },
  })
}

export function useDiagnose() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api<DiagnosisReport>('/api/v1/master-resume/diagnose', { method: 'POST' }),
    onSuccess: () => {
      track(Events.MASTER_RESUME_DIAGNOSED)
      qc.invalidateQueries({ queryKey: ['master-resume'] })
    },
  })
}

export function useCreateCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api(`/api/v1/master-resume/cards/${type}`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useUpdateCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { id: string; body: Record<string, unknown> }) =>
      api(`/api/v1/master-resume/cards/${type}/${vars.id}`, {
        method: 'PATCH',
        body: JSON.stringify(vars.body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}

export function useDeleteCard(type: CardType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      api(`/api/v1/master-resume/cards/${type}/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['master-resume'] }),
  })
}
