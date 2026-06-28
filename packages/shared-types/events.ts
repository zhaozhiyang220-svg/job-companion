// 强类型 PostHog 事件枚举。前后端共用，禁止字符串硬编码事件名。
// 后续 Plan 在此扩展（注册/上传/解析完成/生成补丁/导出/Coach 点击等）。
export const Events = {
  USER_SIGNED_IN: 'user_signed_in',
  USER_PERSONA_PICKED: 'user_persona_picked',
  DISGUISE_TOGGLED: 'disguise_toggled',
  LOCALE_SWITCHED: 'locale_switched',
  AI_HEALTH_CHECKED: 'ai_health_checked',
  MASTER_RESUME_UPLOAD_STARTED: 'master_resume_upload_started',
  MASTER_RESUME_PARSED: 'master_resume_parsed',
  MASTER_RESUME_DIAGNOSED: 'master_resume_diagnosed',
  INTAKE_STARTED: 'intake_started',
  INTAKE_FINALIZED: 'intake_finalized',
  OPPORTUNITY_CREATED: 'opportunity_created',
  OPPORTUNITY_OPENED: 'opportunity_opened',
  OPPORTUNITY_ARCHIVED: 'opportunity_archived',
} as const

export type EventName = (typeof Events)[keyof typeof Events]
