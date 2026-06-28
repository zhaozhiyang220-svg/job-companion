// 强类型 PostHog 事件枚举。前后端共用，禁止字符串硬编码事件名。
// 后续 Plan 在此扩展（注册/上传/解析完成/生成补丁/导出/Coach 点击等）。
export const Events = {
  USER_SIGNED_IN: 'user_signed_in',
  USER_PERSONA_PICKED: 'user_persona_picked',
  DISGUISE_TOGGLED: 'disguise_toggled',
  LOCALE_SWITCHED: 'locale_switched',
  AI_HEALTH_CHECKED: 'ai_health_checked',
} as const

export type EventName = (typeof Events)[keyof typeof Events]
