'use client'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'

export function useIntakeStart() {
  return useMutation({
    mutationFn: () =>
      api<{ session_id: string; first_question: string }>(
        '/api/v1/master-resume/intake/start',
        { method: 'POST' },
      ),
    onSuccess: () => track(Events.INTAKE_STARTED),
  })
}

export function useIntakeAnswer() {
  return useMutation({
    mutationFn: (vars: { session_id: string; answer: string }) =>
      api<{ done: boolean; next_question?: string }>(
        '/api/v1/master-resume/intake/answer',
        { method: 'POST', body: JSON.stringify(vars) },
      ),
  })
}

export function useIntakeFinalize() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { session_id: string }) =>
      api('/api/v1/master-resume/intake/finalize', {
        method: 'POST',
        body: JSON.stringify(vars),
      }),
    onSuccess: () => {
      track(Events.INTAKE_FINALIZED)
      qc.invalidateQueries({ queryKey: ['master-resume'] })
    },
  })
}
