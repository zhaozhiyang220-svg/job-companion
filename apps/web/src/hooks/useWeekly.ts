'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'

export type WeeklyStats = {
  new_applications?: number
  new_branches?: number
  exports?: number
  coach_inquiries?: number
  total_active_applications?: number
}

export type SuggestedAction = { label: string; url?: string | null }

export type Weekly = {
  id: string
  week_of: string
  stats: WeeklyStats
  ai_observation_text: string
  suggested_actions: SuggestedAction[]
  generated_at: string
}

export type WeeklyHistoryItem = { week_of: string; stats: WeeklyStats }

export function useWeekly(weekOf?: string) {
  return useQuery({
    queryKey: ['weekly', weekOf],
    queryFn: () => api<Weekly>(`/api/v1/weekly${weekOf ? `?week_of=${weekOf}` : ''}`),
  })
}

export function useRefreshWeekly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (weekOf?: string) =>
      api(`/api/v1/weekly/refresh${weekOf ? `?week_of=${weekOf}` : ''}`, { method: 'POST' }),
    onSuccess: () => {
      track(Events.WEEKLY_REFRESHED)
      qc.invalidateQueries({ queryKey: ['weekly'] })
    },
  })
}

export function useWeeklyHistory(weeks = 8) {
  return useQuery({
    queryKey: ['weekly-history', weeks],
    queryFn: () => api<WeeklyHistoryItem[]>(`/api/v1/weekly/history?weeks=${weeks}`),
  })
}
