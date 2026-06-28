'use client'
import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'

export type CoachAvailability = {
  week_of: string
  slots_total: number
  slots_taken: number
  available: boolean
}

export function useCoachAvailability() {
  const q = useQuery({
    queryKey: ['coach-availability'],
    queryFn: () => api<CoachAvailability>('/api/v1/coach/availability'),
  })
  useEffect(() => {
    if (q.data) track(Events.COACH_AVAILABILITY_VIEWED)
  }, [q.data])
  return q
}

export function useCreateInquiry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      application_id?: string
      source_screen: string
      contact_method: string
      notes?: string
    }) =>
      api<{ id: string; available_after_create: boolean }>('/api/v1/coach/inquiries', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (_r, vars) => {
      track(Events.COACH_INQUIRY_SUBMITTED, { source: vars.source_screen })
      qc.invalidateQueries({ queryKey: ['coach-availability'] })
    },
  })
}
