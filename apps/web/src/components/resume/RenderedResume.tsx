'use client'
import type { ReactNode } from 'react'
import { useTranslations } from 'next-intl'
import type { RenderedResumeData } from './types'

export function RenderedResume({
  data,
  highlight = false,
}: {
  data: RenderedResumeData
  highlight?: boolean
}) {
  const t = useTranslations('resume_tab')
  return (
    <div className="space-y-4">
      <Section title={t('section_experience')}>
        {data.experience_cards.map((e) => (
          <Card key={e.id} emphasis={highlight ? e._emphasized : 'none'} hidden={highlight && e._hidden}>
            <div className="font-bold">
              {e.company} — {e.title}
            </div>
            <div className="text-xs text-neutral-500">
              {e.period} · {e.industry}
            </div>
            <div className="text-sm">{e.scope}</div>
            {(e.achievements ?? []).map((a, i) => (
              <div key={i} className="text-sm">
                • {a}
              </div>
            ))}
          </Card>
        ))}
      </Section>
      <Section title={t('section_project')}>
        {data.project_cards.map((p) => (
          <Card
            key={p.id}
            emphasis={highlight ? p._emphasized : 'none'}
            hidden={highlight && p._hidden}
            patched={highlight && (p._patched_fields?.length ?? 0) > 0}
          >
            <div className="font-bold">
              {p.project_name} {p.role && `· ${p.role}`}
            </div>
            <div className="text-xs text-neutral-500">{p.period}</div>
            <ul className="list-disc pl-4 text-sm">
              {p.star?.situation && (
                <li>
                  <b>背景：</b>
                  {p.star.situation}
                </li>
              )}
              {p.star?.task && (
                <li>
                  <b>目标：</b>
                  {p.star.task}
                </li>
              )}
              {p.star?.action && (
                <li>
                  <b>行动：</b>
                  {p.star.action}
                </li>
              )}
              {p.star?.result && (
                <li>
                  <b>结果：</b>
                  {p.star.result}
                </li>
              )}
            </ul>
            {highlight && (p._inserted_keywords?.length ?? 0) > 0 && (
              <div className="mt-1">
                {p._inserted_keywords?.map((k, i) => (
                  <span
                    key={i}
                    className="mr-1 bg-blue-100 px-2 py-0.5 text-xs text-blue-700"
                  >
                    +{k}
                  </span>
                ))}
              </div>
            )}
          </Card>
        ))}
      </Section>
      <Section title={t('section_ability')}>
        <div className="flex flex-wrap gap-2">
          {data.ability_cards.map((a) => (
            <span
              key={a.id}
              className={`border px-2 py-1 text-xs ${
                highlight && a._emphasized === 'high' ? 'border-yellow-400 bg-yellow-100' : 'border-neutral-300'
              } ${highlight && a._hidden ? 'line-through opacity-30' : ''}`}
            >
              {a.skill_name} Lv{a.level}
            </span>
          ))}
        </div>
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 border-b border-black pb-1 font-bold">{title}</h3>
      {children}
    </div>
  )
}

function Card({
  children,
  emphasis,
  hidden,
  patched,
}: {
  children: ReactNode
  emphasis?: string
  hidden?: boolean
  patched?: boolean
}) {
  if (hidden) return <div className="border border-neutral-200 p-2 line-through opacity-30">{children}</div>
  const bg =
    emphasis === 'high'
      ? 'border-yellow-400 bg-yellow-50'
      : emphasis === 'medium'
        ? 'bg-yellow-50/50 border-neutral-200'
        : patched
          ? 'border-blue-300 bg-blue-50'
          : 'border-neutral-200'
  return <div className={`border p-3 ${bg}`}>{children}</div>
}
