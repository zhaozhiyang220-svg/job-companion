export type Star = { situation: string; task: string; action: string; result: string }

export type RenderedAbility = {
  id: string
  skill_name: string
  level: number
  _emphasized?: string
  _hidden?: boolean
}

export type RenderedProject = {
  id: string
  project_name: string
  role: string
  period: string
  star: Star
  tech_stack?: string[]
  _emphasized?: string
  _hidden?: boolean
  _patched_fields?: string[]
  _inserted_keywords?: string[]
}

export type RenderedExperience = {
  id: string
  company: string
  title: string
  period: string
  industry?: string
  scope: string
  achievements?: string[]
  is_current?: boolean
  _emphasized?: string
  _hidden?: boolean
  _inserted_keywords?: string[]
}

export type RenderedResumeData = {
  ability_cards: RenderedAbility[]
  project_cards: RenderedProject[]
  experience_cards: RenderedExperience[]
}

export type Reasoning = { op_index: number; reason: string }

export type BranchSummary = {
  id: string
  version_label: string
  match_score: number | null
  language: string
  created_at: string
  is_active: boolean
}

export type BranchDetail = BranchSummary & {
  patch: Record<string, unknown>[]
  ai_reasoning: Reasoning[]
  rendered_resume: RenderedResumeData
  master_snapshot: RenderedResumeData
}
