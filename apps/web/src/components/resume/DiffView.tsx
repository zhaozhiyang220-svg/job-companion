'use client'
import { RenderedResume } from './RenderedResume'
import type { RenderedResumeData } from './types'

export function DiffView({ rendered }: { rendered: RenderedResumeData }) {
  return <RenderedResume data={rendered} highlight />
}
