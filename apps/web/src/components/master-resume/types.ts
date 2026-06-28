export type AbilityCard = {
  id: string
  skill_name: string
  level: number
  evidence_text: string
  is_weak: boolean
}

export type ProjectCard = {
  id: string
  project_name: string
  role: string
  period: string
  star: { situation: string; task: string; action: string; result: string }
  is_weak: boolean
  weak_reasons: string[]
}

export type ExperienceCard = {
  id: string
  company: string
  title: string
  period: string
  scope: string
  is_current: boolean
}

export type MasterResumeData = {
  ability_cards: AbilityCard[]
  project_cards: ProjectCard[]
  experience_cards: ExperienceCard[]
  quality_score: number | null
}
