'use client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Events } from '@jc/shared-types'
import { api } from '@/lib/api'
import { track } from '@/lib/posthog'

export type ResourceType =
  | 'interview_recall'
  | 'company_intel'
  | 'recruiter_bg'
  | 'industry_doc'
  | 'other'

export type Signal = { type: string; content: string }

export type Resource = {
  id: string
  type: ResourceType
  title: string
  content_text: string
  source_url: string | null
  tags: string[]
  ai_summary: string
  ai_extracted_signals: Signal[]
  linked_company_names: string[]
  created_at: string
}

export type Collection = {
  id: string
  name: string
  description: string
  created_at: string
  item_count: number
}

export type CreateResourceBody = {
  type: ResourceType
  title: string
  content_text?: string
  source_url?: string
  tags?: string[]
}

export function useResources(params: { type?: string; collection_id?: string } = {}) {
  const search = new URLSearchParams()
  if (params.type) search.set('type', params.type)
  if (params.collection_id) search.set('collection_id', params.collection_id)
  const qs = search.toString()
  return useQuery({
    queryKey: ['resources', params],
    queryFn: () =>
      api<{ items: Resource[]; total: number }>(`/api/v1/resources${qs ? `?${qs}` : ''}`),
  })
}

export function useCreateResource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateResourceBody) =>
      api<Resource>('/api/v1/resources', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      track(Events.RESOURCE_CREATED)
      qc.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}

export function useDeleteResource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api(`/api/v1/resources/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      track(Events.RESOURCE_DELETED)
      qc.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}

export function useCollections() {
  return useQuery({
    queryKey: ['collections'],
    queryFn: () => api<Collection[]>('/api/v1/resource-collections'),
  })
}

export function useCreateCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; description?: string }) =>
      api('/api/v1/resource-collections', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      track(Events.COLLECTION_CREATED)
      qc.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      api(`/api/v1/resource-collections/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['collections'] })
      qc.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}

export function useLinkToCollection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { cid: string; rid: string }) =>
      api(`/api/v1/resource-collections/${vars.cid}/items/${vars.rid}`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resources'] })
      qc.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useApplicationResources(appId: string) {
  return useQuery({
    queryKey: ['app-resources', appId],
    queryFn: () => api<Resource[]>(`/api/v1/applications/${appId}/resources`),
    enabled: Boolean(appId),
  })
}

export function useLinkResourceToApp(appId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (rid: string) =>
      api(`/api/v1/applications/${appId}/resources/${rid}`, { method: 'POST' }),
    onSuccess: () => {
      track(Events.RESOURCE_LINKED_TO_APP, { appId })
      qc.invalidateQueries({ queryKey: ['app-resources', appId] })
    },
  })
}
