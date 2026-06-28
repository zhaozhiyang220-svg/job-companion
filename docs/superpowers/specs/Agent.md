# 开发指令

## 项目概述
求职作战中心 Job Companion v1：Web 工作台，针对在职跳槽/应届/转行三类求职者。
**心智**：主简历是 master，每个 JD 是一个 patch 分支。
**技术栈**：Next.js 15 (TS) + FastAPI (Python 3.11) + Postgres + Redis + S3 + LiteLLM（统一调用 **MiniMax**）。
**完整设计文档**：`docs/superpowers/specs/2026-06-27-job-companion-design.md`（spec）+ `PRD.md` + `TECH_DESIGN.md`
**实施 plan**：`docs/superpowers/plans/2026-06-27-plan-0..7-*.md`（81 task 已拆分到 step 级别）

## 开发规范

### 通用
- 一律走 plan 文档里已拆好的 task，不要自作主张加 step
- 严格 TDD：先写失败测试 → 实现 → 跑通 → commit；每 step 2-5 分钟
- 函数式组件 + Hooks；后端 service 函数为主，避免大类
- 文件保持小而专一；单文件超 300 行先思考是否要拆
- 注释只写"为什么"，不写"是什么"

### 强制约束（违反必拒）
- **TypeScript strict mode 全开**，禁 `any`；Python `mypy --strict`，禁 `Any` 出现在函数签名
- **i18n 硬规则**：用户可见文案禁止硬编码，必须走 `useTranslations` + `messages/{zh,en}.json`
- **AI 调用必须走 `LLMClient.acomplete()`**，禁直接调 `litellm.acompletion` 或 SDK；必传 `user_id` + `scene`
- **加密字段不许明文存**：email / phone / `current_company` 走 `encrypt_field()`；查询用 `email_lookup_hash`
- **Pydantic 严格校验**：所有 endpoint 入参/出参用 Pydantic 模型，禁 `dict[str, Any]` 出现在签名
- **PostHog 事件名走强类型枚举**：`packages/shared-types/events.ts`，禁字符串硬编码
- **PatchOperation 单字段改写幅度 ≤ 30%**：超过抛 `RewriteTooLargeError`，禁绕过
- **现公司经历（`is_current=true`）UI 必须显示强提示组件**，导出 PDF 默认脱敏

### 数据模型规矩
- 数据中心是 `Application`，不是 `Resume`——加新模块时先想清楚归属
- `ResumeBranch.patch` 存 `PatchOperations` 序列，**不存全量快照**
- 主简历存原子卡片（AbilityCard / ProjectCard / ExperienceCard），不存大段文本
- 资源 ↔ 机会、资源 ↔ 合集均为多对多，走 link 表

## 设计要求
- 响应式可看（手机能浏览），不强求可编辑——v1 主战场是桌面浏览器
- 严肃工作场景的视觉：克制、信息密度高、不花哨
- 关键交互必有反馈（loading / success / error），错误信息要可执行
- 所有破坏性操作（删除、归档、回滚）必须二次确认

## AI / Prompt 规则
- Prompt 文件放 `apps/api/src/ai/prompts/*.py`，统一 `*_SYSTEM` 常量 + `build_user_prompt()` 函数
- 输出要求严格 JSON 的 prompt 必须明示"仅输出 JSON，无 markdown，无 ``` 包裹"
- 重操作用 `auto-m1`（MiniMax-M1），轻操作用 `auto-light`（abab6.5s-chat）——不许混用
- 涉及主简历的调用必须启用 **MiniMax Context Caching**（缓存 master 序列化前缀，命中后只计费增量）
- AI 输出语言跟随用户选择的 `output_language`，不许强制中文

## 注意事项
- **隐私优先**：日志禁打印 email / phone / wechat_openid / 简历原文；S3 链接必须用预签名
- **AI 成本控制**：三级开关（单用户日上限 / 总日上限 / 红线熔断）；新增 AI 调用必须先估算月成本
- **容量门**：触达上限统一走 `<CapacityGate code, onClose>` 组件 → 转 Coach 导流，禁直接报错弹窗
- **不主动爬取**：v1 默认仅手动粘贴 JD，禁加爬虫
- **不做的事**：模板市场 / 移动 App / 小程序 / 内推社区 / 团队账号 / 订阅会员——发现 plan 之外的请求先停下问

## 测试约束
- 接口测试跑真实 Postgres（Docker 起），不许 mock SQLAlchemy
- AI 调用必须 mock：`patch("path._llm.acomplete", AsyncMock(return_value=json.dumps(...)))`
- 每个 plan 至少 1 个 Playwright e2e 关键路径冒烟，CI 必跑
- 测试只测对外行为，不测实现细节（方法名 / SQL 字符串）

## 提交与分支
- 一 task 一 PR；commit message 遵循 `feat(scope): ...` / `fix(scope): ...` / `chore(scope): ...`
- 每个 commit 必过 CI（lint + typecheck + test + e2e）
- 不许 `--no-verify` 跳 hook；不许 force-push 到 main
- 任何 Alembic migration 必须实现 `downgrade()`，上线前在 staging 演练一次

## 三个闸门
**每开始一个 task 前必须明确回答**：

1. **会改哪些文件、不改哪些文件**——列出 Create / Modify / Test 路径清单（plan 文档里已写明，照抄即可）
2. **本轮交付的可验证增量是什么**——必须能跑 1 条测试或 1 条 curl 命令证明它工作
3. **回滚方案是什么**——`git revert <sha>` 是否安全？涉及 migration 时 `alembic downgrade -1` 是否真能跑通？

三问任一答不出来 → 不许开始写代码。
