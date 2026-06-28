'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export type ApplicationStatus = 'drafting' | 'archived'

export type ApplicationListItem = {
  id: string
  status: string
  company_name: string
  job_title: string
  department: string
  salary_range: string
  last_active_at: string
}

export type ApplicationList = {
  items: ApplicationListItem[]
  total: number
  page: number
  page_size: number
}

export type JobPosting = {
  company_name: string
  job_title: string
  department: string
  salary_range: string
  location: string
  language: string
  requirements_parsed: { hard?: string[]; soft?: string[]; years?: string }
  hidden_preferences: string[]
  red_flags: string[]
  raw_text: string
  source_url: string | null
}

export type ApplicationDetail = {
  id: string
  status: string
  priority: number
  notes: string
  created_at: string
  last_active_at: string
  job_posting: JobPosting
}

export function useApplications(status?: ApplicationStatus) {
  return useQuery({
    queryKey: ['applications', status],
    queryFn: () =>
      api<ApplicationList>(
        `/api/v1/applications${status ? `?status=${status}` : ''}`,
      ),
  })
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: ['application', id],
    queryFn: () => api<ApplicationDetail>(`/api/v1/applications/${id}`),
    enabled: Boolean(id),
  })
}

export function useCreateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { raw_text: string; source_url?: string }) =>
      api<ApplicationDetail>('/api/v1/applications', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
  })
}

export function useUpdateApplication(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { status?: string; priority?: number; notes?: string }) =>
      api(`/api/v1/applications/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      qc.invalidateQueries({ queryKey: ['application', id] })
    },
  })
}
