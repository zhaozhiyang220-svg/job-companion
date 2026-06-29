'use client'
import { useTranslations } from 'next-intl'
import { AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SectionLabel } from '@/components/ui/section-label'
import { cn } from '@/lib/utils'

export type DimScore = { score: number; comment: string }
export type DiagnosisReport = {
  target_industry: string
  structure: {
    module_completeness: DimScore
    module_order: DimScore
    length_control: DimScore
    readability: DimScore
    composite_score: number
  }
  ats: {
    format_risks: string[]
    keyword_density_comment: string
    missing_keywords: string[]
    weak_verbs: { ratio_pct: number; comment: string; examples: string[] }
  }
  highlights_issues: { issues: string[]; highlights: string[] }
  industry_benchmark: { dimension: string; expected: string; current: string; gap: string }[]
  fix_priorities: { urgent: string[]; important: string[]; nice_to_have: string[] }
  qualified: boolean
}

function Dots({ n }: { n: number }) {
  return (
    <span className="inline-flex gap-0.5" aria-label={`${n}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={cn('h-2 w-2', i <= n ? 'bg-accent' : 'bg-bg-muted')}
          aria-hidden="true"
        />
      ))}
    </span>
  )
}

function Block({ children }: { children: React.ReactNode }) {
  return <div className="border border-border p-5">{children}</div>
}

export function DiagnosisReportView({
  report,
  onRebuild,
}: {
  report: DiagnosisReport
  onRebuild?: () => void
}) {
  const t = useTranslations('diagnosis')
  const s = report.structure
  const dims: [string, DimScore][] = [
    [t('dim_completeness'), s.module_completeness],
    [t('dim_order'), s.module_order],
    [t('dim_length'), s.length_control],
    [t('dim_readability'), s.readability],
  ]
  const score = s.composite_score

  return (
    <div className="space-y-6">
      {/* 头部：综合分 + 目标行业 */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-fg pb-4">
        <div>
          <SectionLabel num="00">{t('report_title')}</SectionLabel>
          <p className="mt-2 text-sm text-fg-muted">
            {t('target_industry')}：<span className="text-fg">{report.target_industry || '—'}</span>
          </p>
        </div>
        <div className="text-right">
          <div className="label-xs text-fg-muted">{t('composite')}</div>
          <div
            className={cn(
              'mono text-4xl font-bold tabular-nums',
              report.qualified ? 'text-fg' : 'text-destructive',
            )}
          >
            {score}
            <span className="text-base text-fg-muted">/100</span>
          </div>
        </div>
      </div>

      {/* 不合格横幅 */}
      {!report.qualified && (
        <div className="flex flex-wrap items-center justify-between gap-3 border border-accent bg-accent-soft p-4">
          <div className="flex items-start gap-2 text-sm">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" aria-hidden="true" />
            <span>{t('unqualified_banner', { score })}</span>
          </div>
          {onRebuild && (
            <Button variant="accent" size="sm" onClick={onRebuild}>
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              {t('rebuild_cta')}
            </Button>
          )}
        </div>
      )}

      {/* 一、整体结构 */}
      <section className="space-y-3">
        <SectionLabel num="01">{t('s1_structure')}</SectionLabel>
        <Block>
          <div className="space-y-3">
            {dims.map(([label, d]) => (
              <div key={label} className="flex flex-wrap items-center gap-3 text-sm">
                <span className="w-24 shrink-0 font-medium">{label}</span>
                <Dots n={d.score} />
                <span className="flex-1 text-fg-muted">{d.comment}</span>
              </div>
            ))}
          </div>
        </Block>
      </section>

      {/* 二、ATS */}
      <section className="space-y-3">
        <SectionLabel num="02">{t('s2_ats')}</SectionLabel>
        <Block>
          <dl className="space-y-3 text-sm">
            <Row label={t('ats_format_risks')}>
              {report.ats.format_risks.length ? (
                <ul className="list-disc pl-4">
                  {report.ats.format_risks.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-fg-subtle">{t('none')}</span>
              )}
            </Row>
            <Row label={t('ats_keyword_density')}>
              <span className="text-fg-muted">{report.ats.keyword_density_comment || '—'}</span>
            </Row>
            <Row label={t('ats_missing_keywords')}>
              <div className="flex flex-wrap gap-1">
                {report.ats.missing_keywords.length ? (
                  report.ats.missing_keywords.map((k, i) => (
                    <span key={i} className="mono border border-accent bg-accent-soft px-2 py-0.5 text-xs text-accent">
                      {k}
                    </span>
                  ))
                ) : (
                  <span className="text-fg-subtle">{t('none')}</span>
                )}
              </div>
            </Row>
            <Row label={t('ats_weak_verbs')}>
              <span className="text-fg-muted">
                <span className="mono text-fg">{report.ats.weak_verbs.ratio_pct}%</span>{' '}
                {report.ats.weak_verbs.comment}
                {report.ats.weak_verbs.examples.length > 0 &&
                  `（${report.ats.weak_verbs.examples.join('、')}）`}
              </span>
            </Row>
          </dl>
        </Block>
      </section>

      {/* 三、亮点与硬伤 */}
      <section className="space-y-3">
        <SectionLabel num="03">{t('s3_highlights')}</SectionLabel>
        <div className="grid gap-4 md:grid-cols-2">
          <Block>
            <div className="mb-2 flex items-center gap-2 font-medium text-destructive">
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              {t('issues')}
            </div>
            <BulletList items={report.highlights_issues.issues} empty={t('none')} dot="bg-destructive" />
          </Block>
          <Block>
            <div className="mb-2 flex items-center gap-2 font-medium text-success">
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
              {t('highlights')}
            </div>
            <BulletList items={report.highlights_issues.highlights} empty={t('none')} dot="bg-success" />
          </Block>
        </div>
      </section>

      {/* 四、行业对标 */}
      <section className="space-y-3">
        <SectionLabel num="04">{t('s4_benchmark')}</SectionLabel>
        <Block>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-fg text-left">
                  <th className="mono py-2 pr-4 text-xs uppercase tracking-wider text-fg-muted">
                    {t('bench_dimension')}
                  </th>
                  <th className="mono py-2 pr-4 text-xs uppercase tracking-wider text-fg-muted">
                    {t('bench_expected')}
                  </th>
                  <th className="mono py-2 pr-4 text-xs uppercase tracking-wider text-fg-muted">
                    {t('bench_current')}
                  </th>
                  <th className="mono py-2 text-xs uppercase tracking-wider text-fg-muted">
                    {t('bench_gap')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {report.industry_benchmark.map((b, i) => (
                  <tr key={i} className="border-b border-border align-top">
                    <td className="py-3 pr-4 font-medium">{b.dimension}</td>
                    <td className="py-3 pr-4 text-fg-muted">{b.expected}</td>
                    <td className="py-3 pr-4 text-fg-muted">{b.current}</td>
                    <td className="py-3 text-fg-muted">{b.gap}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Block>
      </section>

      {/* 五、修复优先级 */}
      <section className="space-y-3">
        <SectionLabel num="05">{t('s5_priorities')}</SectionLabel>
        <div className="space-y-3">
          <Priority dot="bg-destructive" label={t('prio_urgent')} items={report.fix_priorities.urgent} empty={t('none')} />
          <Priority dot="bg-accent" label={t('prio_important')} items={report.fix_priorities.important} empty={t('none')} />
          <Priority dot="bg-fg-subtle" label={t('prio_nice')} items={report.fix_priorities.nice_to_have} empty={t('none')} />
        </div>
      </section>
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:gap-4">
      <dt className="w-28 shrink-0 font-medium">{label}</dt>
      <dd className="flex-1">{children}</dd>
    </div>
  )
}

function BulletList({ items, empty, dot }: { items: string[]; empty: string; dot: string }) {
  if (!items.length) return <p className="text-sm text-fg-subtle">{empty}</p>
  return (
    <ul className="space-y-1.5 text-sm">
      {items.map((x, i) => (
        <li key={i} className="flex items-start gap-2">
          <span className={cn('mt-1.5 h-1.5 w-1.5 flex-shrink-0', dot)} aria-hidden="true" />
          <span>{x}</span>
        </li>
      ))}
    </ul>
  )
}

function Priority({
  dot,
  label,
  items,
  empty,
}: {
  dot: string
  label: string
  items: string[]
  empty: string
}) {
  return (
    <div className="border border-border p-4">
      <div className="mb-2 flex items-center gap-2 font-medium">
        <span className={cn('h-2.5 w-2.5', dot)} aria-hidden="true" />
        {label}
      </div>
      <BulletList items={items} empty={empty} dot={dot} />
    </div>
  )
}
