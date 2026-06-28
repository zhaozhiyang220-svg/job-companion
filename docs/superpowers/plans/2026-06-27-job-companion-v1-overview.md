# 求职作战中心 v1 · 8 个 Plan 高阶 Outline

> **状态**：Outline（中观地图），非可执行 plan
> **对应 spec**：`docs/superpowers/specs/2026-06-27-job-companion-design.md`
> **总估时**：16-18 周（个人独开），略超 3-4 月窗口，无 buffer

---

## 技术栈固化

| 层 | 技术 |
|---|---|
| 前端 | Next.js 15 (TypeScript, App Router) + Tailwind CSS + shadcn/ui |
| i18n | next-intl（路由 + 翻译） |
| 后端 | FastAPI (Python 3.11+) + Pydantic v2 |
| ORM | SQLAlchemy 2.0 + Alembic（迁移） |
| DB | Postgres 16（生产用 Supabase 或自托管） |
| 缓存/限流 | Redis（轻量用法） |
| 文件存储 | S3 兼容（生产 Cloudflare R2 / 阿里 OSS） |
| AI 抽象 | LiteLLM（**用户侧统一调用 MiniMax**：M1 重活 + abab6.5s 轻活；同家族两档兜底） |
| PDF 生成 | WeasyPrint（HTML → PDF，中英都好用） |
| 简历解析 | pypdfium2 + python-docx + LLM 结构化抽取 |
| 鉴权 | 微信开放平台扫码 + Magic Link（邮箱） |
| 部署 | 前端 Vercel · 后端 Fly.io / 阿里云 ECS · 数据库 Supabase |
| 监控 | Sentry + 自建成本仪表盘 |
| 行为分析 | **PostHog Cloud**（免费层 1M events/月，自托管可选） |
| e2e 测试 | **Playwright**（多浏览器，CI 跑关键路径冒烟） |

---

## 仓库结构（pnpm monorepo）

```
job-companion/
├── apps/
│   ├── web/                    # Next.js 前端
│   │   ├── src/
│   │   │   ├── app/[locale]/   # i18n 路由
│   │   │   ├── components/
│   │   │   ├── lib/
│   │   │   └── i18n/
│   │   └── tests/
│   └── api/                    # FastAPI 后端
│       ├── src/
│       │   ├── routers/
│       │   ├── services/
│       │   ├── models/         # SQLAlchemy
│       │   ├── schemas/        # Pydantic
│       │   ├── ai/             # LiteLLM 抽象（provider=MiniMax） + prompts
│       │   └── core/
│       ├── alembic/
│       └── tests/
├── packages/
│   └── shared-types/           # 由 FastAPI OpenAPI 自动生成 TS 类型
├── infra/
│   ├── docker-compose.yml      # 本地 postgres + redis
│   └── deploy/
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── .github/workflows/          # CI: lint/test/typecheck
├── pnpm-workspace.yaml
└── README.md
```

---

## 8 Plan 依赖图

```
                 ┌──────────────────────┐
                 │ Plan 0: 基础设施     │  ←必须最先完成
                 │ 仓库/CI/auth/i18n/壳 │
                 └─────────┬────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
   ┌─────────────────┐ ┌────────────┐ ┌──────────────┐
   │Plan 1:          │ │Plan 4:     │ │Plan 7:       │
   │MasterResume     │ │Resource    │ │Coach +       │
   │上传/解析/卡片   │ │资源库      │ │成本仪表盘    │
   └────────┬────────┘ └──────┬─────┘ └──────────────┘
            │                 │
            ▼                 │
   ┌─────────────────┐        │
   │Plan 2:          │        │
   │Application+JD   │◄───────┘ (资源可挂载到机会)
   │求职机会列表     │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │Plan 3:          │
   │ResumeBranch     │◄────────► 简历定制核心
   │PatchOps+diff+PDF│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │Plan 5:          │
   │Investment(轻)   │
   │+ 投递记录 Tab   │
   └─────────────────┘
            │
            ▼
   ┌─────────────────┐
   │Plan 6:          │
   │WeeklyDigest     │
   │本周复盘+AI 观察 │
   └─────────────────┘
```

**推荐开发顺序**：0 → 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## Plan 0：基础设施 + 项目骨架

**Goal**：从空仓库到"可登录、能切中英、能切伪装界面、CI 跑通、本地能 dev"

**Scope**
- pnpm monorepo + apps/web (Next.js) + apps/api (FastAPI) + Docker Compose 本地环境
- Postgres + Alembic 初始化
- 微信扫码登录 + 邮箱 Magic Link（持久 session）
- 用户表（含 persona_type 选择 onboarding）
- next-intl 双语骨架（zh / en）
- 顶层导航壳 + 5 个一级入口路由（页面留空）
- 伪装界面（番茄钟 + 待办 mock UI）+ 全局快捷键
- CI：lint / typecheck / test / e2e
- Sentry 接入
- **PostHog 接入 + 事件枚举骨架**
- **Playwright e2e 框架 + 1 个 smoke test**
- LiteLLM 配置（provider=MiniMax，国内/海外双 endpoint）+ `/api/v1/health/ai` 健康检查接口

**Out of scope**：业务模块（留给 Plan 1+）

**Files**（关键）
- `apps/web/src/app/[locale]/layout.tsx`、`(auth)/login/page.tsx`、`(app)/dashboard/page.tsx` 等
- `apps/web/src/components/{nav,disguise}`
- `apps/api/src/routers/{auth,health}.py`
- `apps/api/src/models/user.py`
- `apps/api/src/core/{config,db,security,llm}.py`
- `apps/api/alembic/versions/0001_initial.py`
- `infra/docker-compose.yml`
- `.github/workflows/ci.yml`

**Tasks 估计**：18-22 个 bite-sized

**估时**：2-3 周

---

## Plan 1：MasterResume 模块

**Goal**：用户能上传简历 → AI 解析为 AbilityCard/ProjectCard/ExperienceCard → 校对/编辑/补充 → 含金量诊断

**Scope**
- 文件上传（S3 预签名）+ PDF/Docx 文本抽取
- LLM 结构化抽取（MiniMax-M1）→ 三类卡片
- 卡片 CRUD UI（含 is_weak 标注）
- 应届生轻问诊（5-8 轮对话，abab6.5s-chat）
- 转行人卡片打标 cross_domain（v1 仅打标，映射逻辑在 Plan 3）
- 含金量诊断（独立 endpoint）
- 现公司（is_current）UI 强提示

**依赖**：Plan 0

**Out of scope**：简历定制（Plan 3）、AI 跨域映射逻辑（Plan 3）

**Files**（关键）
- `apps/api/src/models/{master_resume,cards}.py`
- `apps/api/src/services/{resume_parser,quality_diagnoser,interview_intake}.py`
- `apps/api/src/ai/prompts/{parse_resume,diagnose_quality,intake_dialogue}.py`
- `apps/api/src/routers/master_resume.py`
- `apps/web/src/app/[locale]/(app)/master-resume/`
- `apps/web/src/components/cards/{AbilityCard,ProjectCard,ExperienceCard}.tsx`

**Tasks 估计**：22-28 个

**估时**：3 周

---

## Plan 2：Application + JobPosting 模块

**Goal**：用户能"新增求职机会"（粘 JD 文本/链接）→ AI 解析 JD → 看到求职机会列表 → 进入单机会的 5 列 Tab 壳（只亮简历列）

**Scope**
- 求职机会 CRUD + 列表筛选（全部/进行中/已归档）
- JD 粘贴解析（abab6.5s-chat）→ 公司/岗位/薪资/硬技能/软技能/隐性偏好/雷区
- 单机会 5 列 Tab 壳（简历列 lit + Plan 5 投递列 lit；其他 3 列灰显 + 路线图提示）
- 资源关联入口（多对多挂载，UI 雏形）
- 容量限制：≤ 20 进行中、≤ 15 月新建（超限提示 Coach 导流）

**依赖**：Plan 0、Plan 1（机会卡片渲染需引用主简历状态）

**Out of scope**：补丁分支生成（Plan 3）、投递动作（Plan 5）、资源 CRUD（Plan 4）

**Files**（关键）
- `apps/api/src/models/{application,job_posting}.py`
- `apps/api/src/services/jd_parser.py`
- `apps/api/src/ai/prompts/parse_jd.py`
- `apps/api/src/routers/application.py`
- `apps/web/src/app/[locale]/(app)/opportunities/{page,[id]/layout,[id]/page}.tsx`

**Tasks 估计**：16-20 个

**估时**：2 周

---

## Plan 3：ResumeBranch + PatchOperations 模块（核心）

**Goal**：单机会内"简历定制"模块完整可用——基于主简历生成补丁、并排 diff、保存版本、中英 PDF 导出

**Scope**
- PatchOperations DSL 定义 + apply 函数（主版本 + ops → 渲染版本）
- 补丁生成服务（MiniMax-M1 + MiniMax Context Caching）
- AI 修改理由透明化（每个 op 一条理由）
- 并排双视图渲染（diff 高亮 / 并排 / 合并三种模式切换）
- 评分服务（abab6.5s-chat）
- 版本管理（v1/v2/v3... 可回滚）
- 修改幅度上限（单字段改写 ≤ 30% 字数）
- 中英简历模板（各 1，HTML → WeasyPrint PDF）
- 转行人跨域映射触发（v1.5 留接口，v1 用基础映射）
- 导出时现公司默认脱敏 UI

**依赖**：Plan 0、Plan 1、Plan 2

**Out of scope**：英文措辞地道度评分（v1.5）、转行深度跨域映射（v1.5）、模板市场

**Files**（关键）
- `apps/api/src/models/{resume_branch,patch_op}.py`
- `apps/api/src/services/{patch_generator,patch_applier,resume_scorer,pdf_renderer}.py`
- `apps/api/src/ai/prompts/{generate_patch,score_resume}.py`
- `apps/api/src/templates/resume/{zh_simple,en_simple}.html`
- `apps/web/src/app/[locale]/(app)/opportunities/[id]/resume/page.tsx`
- `apps/web/src/components/resume/{DiffView,SideBySide,MergePreview,PatchReasoning}.tsx`

**Tasks 估计**：28-35 个（最大的 plan）

**估时**：3-4 周

---

## Plan 4：ResourceItem + Collection 模块

**Goal**：用户能往资源库添加面经/公司情报，分合集管理，关联到机会，AI 自动摘要并提取信号

**Scope**
- 资源 CRUD（type/title/content/url/attachments/tags）
- ResourceCollection（合集）CRUD
- 资源 ↔ 机会、资源 ↔ 公司 多对多关联
- AI 摘要 + 信号提取（abab6.5s-chat）
- 在简历定制（Plan 3）页面侧栏可拉取已关联资源作为上下文（在 Plan 3 完成后回过来 wire 一次）
- 容量：≤ 100 资源、≤ 5 合集

**依赖**：Plan 0；与 Plan 2/3 弱耦合（关联接口）

**Out of scope**：资源搜索、推荐资源、社区分享

**Files**（关键）
- `apps/api/src/models/{resource_item,resource_collection}.py`
- `apps/api/src/services/resource_processor.py`
- `apps/api/src/ai/prompts/summarize_resource.py`
- `apps/api/src/routers/resource.py`
- `apps/web/src/app/[locale]/(app)/resources/`

**Tasks 估计**：18-22 个

**估时**：2 周

---

## Plan 5：Investment（轻）+ 投递记录 Tab

**Goal**：单机会内"投递记录"Tab 可用——用户能记录"已投/已读/已约面/已收 offer/已拒"动作，并标注使用的简历版本

**Scope**
- Investment 模型 + CRUD
- 投递时间线 UI（按 action_at 倒序）
- 关联 ResumeBranch（自动带出当前 active 版本）
- 渠道字段（Boss/拉勾/官网/内推/其他 free text）
- 5 列 Tab 中"投递记录"列点亮

**依赖**：Plan 0、Plan 2、Plan 3（ResumeBranch 关联）

**Out of scope**：自动同步招聘平台、邮件抓取（v2）

**Files**（关键）
- `apps/api/src/models/investment.py`
- `apps/api/src/routers/investment.py`
- `apps/web/src/app/[locale]/(app)/opportunities/[id]/investments/page.tsx`
- `apps/web/src/components/investment/InvestmentTimeline.tsx`

**Tasks 估计**：10-14 个

**估时**：1 周

---

## Plan 6：WeeklyDigest 本周复盘

**Goal**："本周复盘"一级入口可用——展示本周统计 + AI 本周观察 + 建议下一步动作

**Scope**
- WeeklyDigest 模型（按 week_of 缓存）
- 周统计计算服务（new_apps, new_branches, exports, coach_inquiries）
- AI 本周观察生成（MiniMax-M1，读 7 天活动）
- 建议下一步（actions 列表）
- Cron job：每周一 00:30 预生成上周 digest
- UI：统计卡片 + 观察文本 + 建议 CTA（跳转到对应模块）

**依赖**：Plan 0、Plan 1、Plan 2、Plan 3、Plan 4、Plan 5（需要全部业务数据）

**Out of scope**：自定义复盘周期、订阅推送邮件

**Files**（关键）
- `apps/api/src/models/weekly_digest.py`
- `apps/api/src/services/weekly_digester.py`
- `apps/api/src/ai/prompts/weekly_observation.py`
- `apps/api/src/jobs/weekly_digest_cron.py`
- `apps/web/src/app/[locale]/(app)/weekly/page.tsx`

**Tasks 估计**：14-18 个

**估时**：1.5 周

---

## Plan 7：Coach 导流 + 成本仪表盘（内部）

**Goal**：Coach 询问表单 + 内部 PM 仪表盘上线

**Scope**
- CoachInquiry 模型 + 提交表单（机会页/简历页/容量超限 三处入口）
- 提交后立即 webhook 推送给 PM（飞书/邮件/Telegram 三选一）
- 一周 5 slot 售罄判定 + UI 显示
- 内部成本仪表盘（仅自己访问，简单 password 保护）
  - 4 张图：DAU/MAU · AI 调用量 · 单 user 日均成本 · 总开销
  - 数据来自所有 AI 调用打点表

**依赖**：Plan 0；并联到 Plan 3/4 的导流入口

**Out of scope**：Coach 自动派单系统、coach 自己的工作台

**Files**（关键）
- `apps/api/src/models/{coach_inquiry,ai_call_log}.py`
- `apps/api/src/routers/{coach,internal_dashboard}.py`
- `apps/api/src/services/notifier.py`
- `apps/web/src/components/coach/InquiryDrawer.tsx`
- `apps/web/src/app/[locale]/(internal)/dashboard/page.tsx`

**Tasks 估计**：12-16 个

**估时**：1.5 周

---

## 跨 Plan 全局约束（每个 plan 隐式继承）

- TS strict mode；Python 用 mypy strict
- 所有 endpoint Pydantic schema 严格校验
- 所有 AI 调用必须经 `apps/api/src/ai/llm_client.py` 统一入口，自动打点 `ai_call_log`
- 所有用户敏感字段（手机/邮箱/在职公司名）字段级加密
- i18n：用户可见文案禁止硬编码，必须走 next-intl
- 现公司（is_current=true）相关 UI 必须有强提示组件
- 容量超限统一走 `<CapacityGate />` 组件 → Coach 导流抽屉
- 每个 PR/commit 必须过 CI（lint + typecheck + 涉及模块的测试 + 关键路径 e2e）
- **PostHog 事件埋点**：所有用户关键行为必须打点（注册、上传、解析完成、生成补丁、导出、Coach 点击等），事件名走 `packages/shared-types/events.ts` 强类型枚举
- **e2e 测试覆盖**：每个 plan 至少提供 1 个 Playwright 关键路径冒烟测试，CI 必跑

---

## v1 与 v1.5/v2 的清晰分界

| 项 | v1 | v1.5 | v2+ |
|---|---|---|---|
| 简历模板 | 中英各 1 | 多模板 | 模板市场 |
| 英文措辞地道度 | — | ✅ | — |
| 转行深度跨域映射 | 接口预留 | ✅ | — |
| JD 链接抓取 | — | ✅ | — |
| 浏览器插件 | — | ✅ | — |
| 多 Agent 锐评 | — | — | ✅（付费墙） |
| 面试模块（5 列 #3） | — | — | ✅ |
| 面试复盘（#4） | — | — | ✅ |
| Offer 评估（#5） | — | — | ✅ |
| 小程序 | — | — | ✅ |

---

## 下一步选择

请你 review 这份 outline，告诉我：

1. **Plan 顺序、范围、依赖** 是否 OK？要不要合并/拆分某个 plan？
2. **Plan 估时** 看起来合理吗？哪个你觉得明显偏乐观/悲观？
3. **技术栈细节**（next-intl / WeasyPrint / Supabase / Fly.io 等）有哪些你想换？
4. **跨 Plan 全局约束**是否漏了什么（比如"必须有 e2e 测试"、"接入 PostHog 行为分析"等）？

确认后我开始写 **Plan 0 的执行级详细文档**（包含 exact file paths + exact commands + TDD 步骤 + commit 节奏），保存为 `docs/superpowers/plans/2026-06-27-plan-0-bootstrap.md`，然后你 review 完再写 Plan 1。
