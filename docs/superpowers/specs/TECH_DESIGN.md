# 求职作战中心 Job Companion 技术方案

> **版本**：v1（2026-06-27）
> **对应文档**：
> - 产品 PRD：`docs/superpowers/specs/2026-06-27-job-companion-PRD.md`
> - 产品 Spec：`docs/superpowers/specs/2026-06-27-job-companion-design.md`
> - 实施 Plans：`docs/superpowers/plans/2026-06-27-plan-0..7-*.md`

---

## 1. 技术选型

### 前端技术栈
- **框架**：[Next.js 15](https://nextjs.org/) + [TypeScript 5.6+](https://www.typescriptlang.org/) + App Router
  - 全栈 React 框架，Vercel 一键部署
  - App Router 提供基于 RSC 的现代渲染模型
  - TS strict mode 全开（`tsconfig.json` `"strict": true`）
- **UI 框架**：[Tailwind CSS 3.4](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)
  - Tailwind 提供原子化 CSS，无运行时
  - shadcn/ui 提供可复制无 npm 依赖的高质量组件（Button / Input / Dialog / Card / Toast）
- **国际化**：[next-intl 3.25](https://next-intl-docs.vercel.app/)
  - 路由前缀模式：`/zh/*`、`/en/*`，默认 `zh`
  - 翻译文件按模块 namespace 切分（`messages/zh.json`、`messages/en.json`）
  - 服务端 + 客户端组件都可用 `useTranslations` / `getTranslations`
- **数据请求**：[TanStack Query 5.59](https://tanstack.com/query/latest)
  - 全局 `QueryClientProvider`，默认 staleTime 30s、retry 1
  - 提供 `useQuery` / `useMutation` 钩子，自动失效缓存
- **HTTP 封装**：原生 `fetch` + 自定义 `api()` 包装（`credentials: 'include'` 跨域携带 cookie）
- **行为分析**：[posthog-js 1.179](https://posthog.com/docs)
  - PostHog Cloud 免费层 1M events/月
  - 强类型事件枚举走 `packages/shared-types/events.ts`
- **异常监控**：[@sentry/nextjs 8.36](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
- **e2e 测试**：[Playwright 1.48](https://playwright.dev/)
  - Chromium 项目，CI 必跑关键路径冒烟
- **单元测试**：[Vitest 2](https://vitest.dev/) + [@testing-library/react](https://testing-library.com/)

### 后端技术栈
- **语言**：[Python 3.11+](https://www.python.org/)
- **框架**：[FastAPI 0.115](https://fastapi.tiangolo.com/) + [Uvicorn 0.32](https://www.uvicorn.org/)
  - 自动生成 OpenAPI / Swagger 文档（`/docs`）
  - 原生 async/await，端点 Pydantic schema 强校验
- **数据校验**：[Pydantic v2.9](https://docs.pydantic.dev/2.9/)
  - 所有 endpoint 入参 / 出参 / Settings 均用 Pydantic 模型
- **ORM**：[SQLAlchemy 2.0.36](https://docs.sqlalchemy.org/en/20/) + [Alembic 1.13](https://alembic.sqlalchemy.org/)
  - 新风格 `Mapped[T]` 类型化映射，配 `mypy --strict`
  - Alembic 自动生成迁移，手工 review 后 `upgrade head`
- **DB 驱动**：[psycopg 3.2](https://www.psycopg.org/psycopg3/)（同步，足够 v1）
- **代码质量**：[ruff 0.7](https://docs.astral.sh/ruff/)（lint + format） + [mypy 1.13](https://mypy-lang.org/)
- **测试**：[pytest 8.3](https://pytest.org/) + [pytest-asyncio 0.24](https://pytest-asyncio.readthedocs.io/) + httpx TestClient
- **任务调度**：[APScheduler 3.10](https://apscheduler.readthedocs.io/)（周一 00:30 BJT 预生成本周 digest）

### AI / LLM 集成（统一供应商：MiniMax）
- **统一抽象层**：[LiteLLM 1.51](https://docs.litellm.ai/)
  - 屏蔽不同 provider 差异；v1 配置只填 **MiniMax**（国内 `api.minimax.chat`，海外 `api.minimaxi.chat`），未来如需多供应商扩 provider 配置即可
  - 支持流式、context cache 等高级特性
  - 同家族两档兜底（详见 §5）
- **主模型**：[MiniMax-M1](https://www.minimaxi.com/)（`minimax/MiniMax-M1`）
  - 用于重操作：简历解析、补丁生成、含金量诊断、跨域映射、本周观察
  - 公开价：输入 ¥6/M、输出 ¥24/M（折合约 $0.85/M、$3.4/M）
- **轻模型**：[abab6.5s-chat](https://www.minimaxi.com/)（`minimax/abab6.5s-chat`）
  - 用于轻操作：JD 解析、资源摘要、评分、应届轻问诊
  - 公开价：输入/输出 ¥1/M（折合约 $0.14/M）
- **兜底**：M1 故障/限流时自动降级到 abab6.5s（同一供应商内同家族两档；保持服务可用，质量按场景做有限补偿）
- **缓存策略**：[MiniMax Context Caching](https://www.minimaxi.com/) — 主简历序列化部分作为缓存前缀，命中后缓存部分价格约为原价 1/3（详见 §5）

### 文件处理
- **PDF 文本抽取**：[pypdfium2 4.30](https://github.com/pypdfium2-team/pypdfium2)
- **Word 文本抽取**：[python-docx 1.1](https://python-docx.readthedocs.io/)
- **HTML → PDF 渲染**：[WeasyPrint 62.3](https://weasyprint.org/)
  - 支持中英文混排（思源 + Inter 字体）
  - Linux 需 `libpango`，Windows 需 GTK runtime，已在 README 标注
- **模板引擎**：[Jinja2 3.1](https://jinja.palletsprojects.com/)

### 数据存储
- **关系数据库**：[Postgres 16](https://www.postgresql.org/)
  - 生产用 [Supabase](https://supabase.com/)（托管）
  - 本地用 Docker `postgres:16-alpine`
- **缓存 / 限流**：[Redis 7](https://redis.io/)
  - 单用户 IP 限流、容量门计数器、AI 调用幂等 key
- **对象存储**：S3 兼容
  - 生产：[Cloudflare R2](https://www.cloudflare.com/products/r2/) 或 [阿里云 OSS](https://www.aliyun.com/product/oss)
  - SDK：[boto3 1.35](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
  - 私有 bucket + 24h 预签名 URL
- **字段级加密**：[cryptography 43](https://cryptography.io/en/latest/) 的 Fernet
  - 加密字段：邮箱（`email_encrypted`）、手机、`current_company`

### 鉴权
- **微信开放平台**：扫码登录（`snsapi_login` scope）
- **邮箱 Magic Link**：自建（SMTP 发链接，token 15 分钟过期，hash 存库）
- **会话**：JWT HS256，存 HTTPOnly + SameSite=Lax Cookie，30 天 TTL
- **依赖库**：[python-jose 3.3](https://python-jose.readthedocs.io/)（JWT）+ [passlib 1.7](https://passlib.readthedocs.io/)

### 监控与运维
- **异常**：[Sentry](https://sentry.io/)（web + api）
- **行为分析**：PostHog Cloud
- **成本观测**：自建 `/internal/dashboard`（4 KPI + 3 折线图，SVG 不引图表库）
- **告警**：成本红线触发短信（暂用 [Twilio](https://www.twilio.com/) 或国内[阿里云 SMS](https://www.aliyun.com/product/sms)）

### 部署与 CI/CD
- **前端**：[Vercel](https://vercel.com/)（自动从 GitHub 部署，PR 预览环境）
- **后端**：[Fly.io](https://fly.io/)（生产）或阿里云 ECS（备选大陆部署）
- **DB**：Supabase Postgres + 自动备份
- **CI**：[GitHub Actions](https://github.com/features/actions)
- **本地开发**：[Docker Compose](https://docs.docker.com/compose/) 一键起 postgres + redis + api + web

### 仓库管理
- **Monorepo**：[pnpm 9.12 workspaces](https://pnpm.io/workspaces)
- **Node**：v20.x（`.nvmrc` 锁定）
- **Python**：venv（`apps/api/.venv`），依赖锁在 `pyproject.toml`

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户浏览器（Web 桌面 / 响应式）                 │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ 求职机会      │  │ 主简历库     │  │ 资源库       │  │ 本周复盘   │ │
│  │ + 5 列 Tab   │  │ + 3 类卡片   │  │ + 合集       │  │ + AI 观察  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            伪装界面（番茄钟+待办）— 全局 Ctrl+`                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │ HTTPS / fetch + HTTPOnly cookie
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Vercel CDN（Next.js 15 + next-intl /zh /en）              │
│  - App Router (RSC + Client Components)                                 │
│  - TanStack Query 数据层                                                │
│  - shadcn/ui 组件 + Tailwind                                            │
│  - PostHog SDK + Sentry SDK                                             │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │ /api/v1/* + /internal/*
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend（Fly.io 容器）                        │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Auth Router  │  │ Master       │  │ Application  │  │ Resume     │ │
│  │ 微信/Magic    │  │ Resume Router│  │ Router       │  │ Branch     │ │
│  │ JWT Session  │  │ + Cards      │  │ + JD parse   │  │ + PatchOps │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Resource     │  │ Investment   │  │ Weekly       │  │ Coach +    │ │
│  │ + Collection │  │ Router       │  │ Router       │  │ Internal   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
│  Services 层：                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ resume_      │  │ patch_       │  │ resume_      │  │ weekly_    │ │
│  │ parser       │  │ generator    │  │ scorer       │  │ digester   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ patch_ops    │  │ pdf_renderer │  │ text_        │  │ notifier   │ │
│  │ apply()      │  │ (WeasyPrint) │  │ extractor    │  │ (飞书/TG)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           LLMClient（LiteLLM 抽象，统一打点 ai_call_logs）        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  APScheduler：周一 00:30 BJT cron → weekly digest 预生成                │
└──────┬──────────────────┬────────────────────┬──────────────────┬──────┘
       │                  │                    │                  │
       ▼                  ▼                    ▼                  ▼
┌────────────┐    ┌────────────┐      ┌────────────┐      ┌──────────────┐
│ Postgres   │    │  Redis     │      │ S3 (R2/OSS)│      │ MiniMax LLM  │
│ (Supabase) │    │ (限流/缓存)│      │ + 预签名URL│      │ - M1 (重活)  │
│            │    │            │      │            │      │ - abab6.5s   │
│ - 用户      │    │            │      │ - 简历原件 │      │   (轻活)     │
│ - 简历卡片  │    │            │      │ - PDF 导出 │      │ (via LiteLLM)│
│ - 应用/分支│    │            │      │            │      │              │
│ - 资源/合集│    │            │      │            │      │              │
│ - AI 日志   │    │            │      │            │      │              │
└────────────┘    └────────────┘      └────────────┘      └──────────────┘

         旁路监控：Sentry（异常） + PostHog（行为） + 内部 Dashboard（成本）
```

**架构特点**：

1. **App-centric 数据模型**：核心实体是 `Application`（求职机会），不是 Resume；让 v2 加面试/复盘/Offer 模块无需重构 v1 数据层（只需"加 tab + 实现该 tab"）
2. **主版本 + 补丁分支机制**：`ResumeBranch.patch` 存 PatchOperations 序列（reorder / emphasize / rewrite / hide / insert_keyword）而非全量快照——主版本一改，所有分支自动重算；diff 渲染极快；存储省 ~90%
3. **AI 统一抽象层（单供应商 MiniMax + 同家族两档兜底）**：所有 LLM 调用走 `LLMClient.acomplete()`，自动按场景选模型 + cost 打点；M1 故障/限流时降级到 abab6.5s；MiniMax Context Caching 在补丁生成场景把主简历部分作为缓存前缀，整体成本降 ~70%
4. **隐私优先**：字段级加密（Fernet）、预签名 URL（24h）、现公司导出默认脱敏、全局快捷键伪装界面、`is_current=true` 经历 UI 强提示
5. **i18n 路由 + AI 语言跟随**：next-intl 路由前缀 `/zh /en`，AI prompt 传 `output_language`，简历模板分语言渲染
6. **容量门 = 商业杠杆**：达到上限统一弹 `<CapacityGate>` 组件 → 直接打开 Coach Inquiry Drawer，把"限制"转化为变现入口
7. **可观测性内嵌**：每次 AI 调用自动写 `ai_call_logs`（user_id / scene / model / tokens / cost / latency / status），驱动内部成本仪表盘

---

## 3. 数据存储设计

### Postgres 关系数据库设计（17 张表）

#### `users` 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| email_encrypted | VARCHAR(512) | Fernet 加密邮箱 |
| email_lookup_hash | VARCHAR(64) UNIQUE | sha256(lower(email))，用于唯一查询 |
| wechat_openid | VARCHAR(128) UNIQUE | 微信开放平台 openid |
| nickname | VARCHAR(128) | 用户昵称 |
| persona_type | ENUM | `fresh_grad / job_hopper / career_changer` |
| preferences | JSONB | 伪装模式开关 / 默认语言 / 默认模板 |
| created_at | TIMESTAMPTZ | 创建时间 |
| last_active_at | TIMESTAMPTZ | 最近活跃时间（用于 DAU/MAU 计算） |

#### `magic_link_tokens` 邮箱登录令牌表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| token_hash | VARCHAR(64) UNIQUE | sha256(raw_token) |
| email_lookup_hash | VARCHAR(64) INDEX | 关联用户 |
| expires_at | TIMESTAMPTZ | 15 分钟后过期 |
| consumed_at | TIMESTAMPTZ NULL | 已消费时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `master_resumes` 主简历表（每用户 1 份，UNIQUE user_id）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID FK → users.id, UNIQUE | 关联用户 |
| basic_info | JSONB | 姓名/电话/邮箱/地点/在职状态 |
| parsed_from_file_url | VARCHAR(1024) | 原始上传文件 s3 key |
| quality_score | INTEGER | AI 含金量打分 0-100 |
| updated_at | TIMESTAMPTZ | 自动更新 |

#### `ability_cards` 能力卡表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| master_resume_id | UUID FK | 关联主简历 |
| skill_name | VARCHAR(128) | 能力名 |
| evidence_text | VARCHAR(2048) | 能力证据 |
| level | INTEGER (1-5) | 水平 |
| last_used_year | INTEGER NULL | 最近使用年份 |
| tags | JSONB | 标签数组 |
| is_weak | BOOLEAN | AI 标记的薄弱项 |

#### `project_cards` 项目卡表（v2 面试模块的题库基础）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| master_resume_id | UUID FK | 关联主简历 |
| project_name | VARCHAR(256) | 项目名 |
| role | VARCHAR(128) | 担任角色 |
| period | VARCHAR(64) | 时间段 |
| scale_data | JSONB | 规模数据（用户量/GMV/团队规模等结构化） |
| star | JSONB | `{situation, task, action, result}` |
| tech_stack | JSONB | 技术栈数组 |
| domain_tags | JSONB | 业务域标签数组 |
| is_weak | BOOLEAN | 含金量低 |
| weak_reasons | JSONB | 薄弱原因列表 |
| cross_domain_translation | JSONB | 转行人跨域映射（v1 仅打标） |

#### `experience_cards` 经历卡表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| master_resume_id | UUID FK | 关联主简历 |
| company_encrypted | VARCHAR(1024) | Fernet 加密公司名 |
| period | VARCHAR(64) | 时间段 |
| title | VARCHAR(128) | 职位 |
| scope | VARCHAR(512) | 职责描述 |
| achievements | JSONB | 成就列表 |
| industry | VARCHAR(64) | 行业 |
| is_current | BOOLEAN | 是否现公司（导出脱敏依据） |

#### `applications` 求职机会表（v1 数据中心）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID FK INDEX | 关联用户 |
| status | ENUM INDEX | `drafting / archived`（v2 扩 applied/interviewing/offered/rejected） |
| priority | INTEGER (1-5) | 优先级 |
| notes | VARCHAR(1024) | 备注 |
| created_at | TIMESTAMPTZ | 创建时间 |
| last_active_at | TIMESTAMPTZ | 最近活跃（onupdate） |

#### `job_postings` 岗位 JD 表（1:1 内嵌于 application）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| application_id | UUID FK UNIQUE | 关联机会 |
| raw_text | TEXT | JD 原文 |
| source_url | VARCHAR(1024) | 来源链接 |
| company_name | VARCHAR(256) | 公司名（AI 提取） |
| job_title | VARCHAR(256) | 岗位名 |
| department | VARCHAR(128) | 部门 |
| salary_range | VARCHAR(64) | 薪资区间 |
| location | VARCHAR(128) | 工作地点 |
| language | VARCHAR(8) | `zh / en`（AI 自动检测） |
| requirements_parsed | JSONB | `{hard: [], soft: [], years: ""}` |
| hidden_preferences | JSONB | AI 提取的隐性偏好 |
| red_flags | JSONB | AI 提取的雷区 |
| parsed_at | TIMESTAMPTZ | 解析时间 |

#### `resume_branches` 简历补丁分支表（核心）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| application_id | UUID FK INDEX | 关联机会 |
| version_label | VARCHAR(16) | `v1 / v2 / v3 / ...` |
| based_on_master_at | TIMESTAMPTZ | 基于哪个时间点的主版本 |
| patch | JSONB | PatchOperations 数组 |
| ai_reasoning | JSONB | `[{op_index, reason}]` |
| match_score | INTEGER NULL | 对该 JD 的匹配评分 0-100 |
| language | VARCHAR(8) | `zh / en`（输出语言） |
| exported_pdf_urls | JSONB | `[{key, url, language, masked}]` |
| is_active | BOOLEAN | 当前活跃版本（每机会唯一） |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `investments` 投递记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| application_id | UUID FK INDEX | 关联机会 |
| used_resume_branch_id | UUID FK NULL | 使用的简历版本 |
| action_type | ENUM INDEX | `submitted / viewed / interview_scheduled / offer_received / rejected` |
| action_at | TIMESTAMPTZ | 动作时间 |
| channel | VARCHAR(64) | 渠道（Boss/拉勾/官网...） |
| notes | TEXT | 备注 |
| created_at | TIMESTAMPTZ | 记录时间 |

#### `resource_items` 资源库条目表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX | 关联用户 |
| type | ENUM INDEX | `interview_recall / company_intel / recruiter_bg / industry_doc / other` |
| title | VARCHAR(256) | 标题 |
| content_text | TEXT | 原文 |
| source_url | VARCHAR(1024) | 来源 |
| attachments | JSONB | 附件 |
| tags | JSONB | 标签数组 |
| ai_summary | TEXT | AI 摘要 |
| ai_extracted_signals | JSONB | `[{type, content}]` 信号 |
| linked_company_names | JSONB | AI 识别的公司名 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `resource_collections` 资源合集表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX | 关联用户 |
| name | VARCHAR(128) | 合集名 |
| description | TEXT | 描述 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `resource_collection_links` 合集-资源关联表（多对多）
| 字段 | 类型 | 说明 |
|------|------|------|
| collection_id | UUID FK PK | 合集 |
| resource_id | UUID FK PK | 资源 |

#### `application_resource_links` 机会-资源关联表（多对多）
| 字段 | 类型 | 说明 |
|------|------|------|
| application_id | UUID FK PK | 机会 |
| resource_item_id | UUID FK PK | 资源 |

#### `intake_sessions` 应届轻问诊会话表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX | 关联用户 |
| transcript | JSONB | 完整对话历史 `[{role, content}]` |
| finished_at | TIMESTAMPTZ NULL | 完成时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `weekly_digests` 本周复盘表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX | 关联用户 |
| week_of | DATE INDEX | 该周周一日期（北京时区）|
| stats | JSONB | `{new_applications, new_branches, exports, coach_inquiries, total_active_applications}` |
| ai_observation_text | TEXT | AI 本周观察 |
| suggested_actions | JSONB | `[{label, url}]` 建议下一步 |
| generated_at | TIMESTAMPTZ | 生成时间 |

约束：`UNIQUE(user_id, week_of)`

#### `coach_inquiries` Coach 咨询表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX | 关联用户 |
| application_id | UUID NULL | 关联机会（可空） |
| source_screen | VARCHAR(64) | `resume_workspace / capacity_gate / coach_page / weekly_action` |
| contact_method | VARCHAR(128) | 微信号/手机/邮箱 |
| status | ENUM | `new / contacted / scheduled / converted / dropped` |
| notes | TEXT | 备注 |
| created_at | TIMESTAMPTZ INDEX | 创建时间 |

#### `ai_call_logs` AI 调用日志表（成本仪表盘底盘）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PRIMARY KEY | 主键 |
| user_id | UUID INDEX NULL | 关联用户（系统调用为 null） |
| scene | VARCHAR(64) INDEX | `resume_parse / patch_generate / jd_parse / ...` |
| model | VARCHAR(64) | 实际命中的模型名 |
| input_tokens | INTEGER | 输入 token 数 |
| output_tokens | INTEGER | 输出 token 数 |
| cost_usd | NUMERIC(10, 6) | 单次成本（美元） |
| latency_ms | INTEGER | 延迟 |
| status | VARCHAR(16) | `ok / error` |
| error_message | VARCHAR(512) NULL | 错误信息 |
| created_at | TIMESTAMPTZ INDEX | 调用时间 |

### S3 对象存储设计

```
s3://job-companion-prod/
├── users/{user_id}/
│   ├── resumes/{uuid}-{filename}.pdf          # 用户上传简历原件
│   ├── resumes/{uuid}-{filename}.docx
│   └── exports/{branch_id}-{uuid}.pdf         # 简历定制 PDF 导出
└── tmp/                                        # 临时缓冲（可选）
```

- 私有 bucket，禁止公开访问
- 上传走 **预签名 PUT URL**（10 分钟有效）→ 浏览器直传，不经后端
- 下载走 **预签名 GET URL**（24 小时有效，导出 PDF 链接 7 天）
- 对象本身服务端加密（SSE-S3）

### Redis 用法

```
# 单用户 RPM 限流
key: ratelimit:{user_id}:{minute}
value: count
ttl: 60s

# 容量门计数缓存（避免每次 query DB）
key: capacity:active:{user_id}
value: 当前进行中机会数
ttl: 5 分钟

# AI 调用幂等性（防止前端重复请求）
key: ai_idempotency:{request_hash}
value: 已生成的响应
ttl: 30 秒
```

### 字段级加密（Fernet）

```python
from cryptography.fernet import Fernet
# 配置：FIELD_ENCRYPTION_KEY 在 .env，base64-urlsafe 32 字节
# 生成命令：python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

加密字段：
  - users.email_encrypted          (登录主键的明文不留)
  - experience_cards.company_encrypted  (现公司导出脱敏依赖)
  - 未来扩展：phone, salary_actual

不加密但 hash 查询：
  - users.email_lookup_hash = sha256(lower(email))
  - magic_link_tokens.token_hash = sha256(raw_token)
```

---

## 4. API 接口设计

### Pydantic 通用约定

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import StrEnum

# 所有响应基类
class ApiResponse(BaseModel):
    """v1 不强制包装，直接返回数据对象；错误走 HTTPException + JSON detail"""
    pass

# 容量门错误响应
class CapacityError(BaseModel):
    """HTTP 409，detail 字段"""
    code: str       # capacity_active / capacity_monthly / capacity_resources / capacity_collections / coach_full
    message: str

# 全局枚举
class PersonaType(StrEnum):
    FRESH_GRAD = "fresh_grad"
    JOB_HOPPER = "job_hopper"
    CAREER_CHANGER = "career_changer"

class ApplicationStatus(StrEnum):
    DRAFTING = "drafting"
    ARCHIVED = "archived"
    APPLIED = "applied"            # v2 扩
    INTERVIEWING = "interviewing"  # v2 扩
    OFFERED = "offered"            # v3 扩
    REJECTED = "rejected"          # v3 扩
```

### Endpoint 总览

| 模块 | Method | Path | 说明 |
|---|---|---|---|
| **Health** | GET | `/api/v1/health` | 服务健康检查 |
|  | GET | `/api/v1/health/ai` | AI 服务健康检查（调一次 abab6.5s） |
| **Auth** | POST | `/api/v1/auth/magic-link/request` | 请求邮箱登录链接 |
|  | POST | `/api/v1/auth/magic-link/verify` | 验证 token + set cookie |
|  | GET | `/api/v1/auth/wechat/qr` | 获取微信扫码 URL |
|  | GET | `/api/v1/auth/wechat/callback` | 微信回调 + set cookie |
| **Me** | GET | `/api/v1/me` | 当前用户信息 |
|  | PATCH | `/api/v1/me` | 更新 nickname / persona / preferences |
| **MasterResume** | POST | `/api/v1/master-resume/upload-init` | 获取上传预签名 URL |
|  | POST | `/api/v1/master-resume/parse` | 解析已上传文件 |
|  | GET | `/api/v1/master-resume` | 获取当前主简历 |
|  | POST | `/api/v1/master-resume/diagnose` | 触发 AI 含金量诊断 |
|  | POST | `/api/v1/master-resume/cards/{type}` | 新增卡片（ability/project/experience） |
|  | PATCH | `/api/v1/master-resume/cards/{type}/{id}` | 更新卡片 |
|  | DELETE | `/api/v1/master-resume/cards/{type}/{id}` | 删除卡片 |
|  | POST | `/api/v1/master-resume/intake/start` | 应届轻问诊：开始 |
|  | POST | `/api/v1/master-resume/intake/answer` | 应届轻问诊：答复 |
|  | POST | `/api/v1/master-resume/intake/finalize` | 应届轻问诊：完成转主简历 |
| **Applications** | POST | `/api/v1/applications` | 创建求职机会（带 JD 解析） |
|  | GET | `/api/v1/applications?status=&page=` | 列表（分页 + 状态筛选） |
|  | GET | `/api/v1/applications/{id}` | 详情 |
|  | PATCH | `/api/v1/applications/{id}` | 更新（归档/优先级/备注） |
| **ResumeBranches** | POST | `/api/v1/applications/{id}/branches` | AI 生成新补丁分支 |
|  | GET | `/api/v1/applications/{id}/branches` | 列出所有版本 |
|  | GET | `/api/v1/applications/{id}/branches/{bid}` | 单分支详情（含 rendered） |
|  | PATCH | `/api/v1/applications/{id}/branches/{bid}` | 手动覆盖 ops |
|  | DELETE | `/api/v1/applications/{id}/branches/{bid}` | 删除 |
|  | POST | `/api/v1/applications/{id}/branches/{bid}/rollback-to/{pid}` | 回滚 |
|  | POST | `/api/v1/applications/{id}/branches/{bid}/export` | 导出 PDF |
| **Investments** | POST | `/api/v1/applications/{id}/investments` | 新增动作 |
|  | GET | `/api/v1/applications/{id}/investments` | 时间线 |
|  | PATCH | `/api/v1/applications/{id}/investments/{iid}` | 更新 |
|  | DELETE | `/api/v1/applications/{id}/investments/{iid}` | 删除 |
| **Resources** | POST | `/api/v1/resources` | 创建（含 AI 摘要） |
|  | GET | `/api/v1/resources?type=&collection_id=` | 列表 |
|  | GET | `/api/v1/resources/{id}` | 详情 |
|  | PATCH | `/api/v1/resources/{id}` | 更新（content 变化触发重摘要） |
|  | DELETE | `/api/v1/resources/{id}` | 删除 |
| **Collections** | POST | `/api/v1/resource-collections` | 创建合集 |
|  | GET | `/api/v1/resource-collections` | 列表 |
|  | PATCH | `/api/v1/resource-collections/{id}` | 更新 |
|  | DELETE | `/api/v1/resource-collections/{id}` | 删除 |
|  | POST | `/api/v1/resource-collections/{cid}/items/{rid}` | 加入合集 |
|  | DELETE | `/api/v1/resource-collections/{cid}/items/{rid}` | 移出合集 |
| **App-Resource** | POST | `/api/v1/applications/{aid}/resources/{rid}` | 关联 |
|  | DELETE | `/api/v1/applications/{aid}/resources/{rid}` | 解除 |
|  | GET | `/api/v1/applications/{aid}/resources` | 该机会关联的资源 |
| **Weekly** | GET | `/api/v1/weekly?week_of=YYYY-MM-DD` | 本周/指定周 digest |
|  | POST | `/api/v1/weekly/refresh` | 强制重算 |
|  | GET | `/api/v1/weekly/history?weeks=8` | 历史周列表 |
| **Coach** | GET | `/api/v1/coach/availability` | 本周 slot 状态 |
|  | POST | `/api/v1/coach/inquiries` | 提交 Coach 咨询 + 通知 PM |
| **Internal** | GET | `/internal/dashboard/summary` | KPI 概览（含密码） |
|  | GET | `/internal/dashboard/timeseries?days=30` | 时间序列 |

### 关键 Pydantic Schema 示例

```python
# 1. 简历定制：生成补丁分支
class CreateBranchIn(BaseModel):
    language: str | None = None   # 默认跟随 JD.language

class BranchDetail(BaseModel):
    id: UUID
    version_label: str
    match_score: int | None
    language: str
    created_at: datetime
    is_active: bool
    patch: list[dict]              # PatchOperations 序列
    ai_reasoning: list[dict]       # [{op_index, reason}]
    rendered_resume: dict          # apply_operations 结果（含 _emphasized / _hidden 标记）
    master_snapshot: dict          # 同时返回 master，便于 diff 渲染

# 2. PatchOperation 类型定义
class ReorderOp(TypedDict):
    type: Literal["reorder"]
    card_id: str
    new_position: int

class EmphasizeOp(TypedDict):
    type: Literal["emphasize"]
    card_id: str
    intensity: Literal["low", "medium", "high"]

class RewriteOp(TypedDict):
    type: Literal["rewrite"]
    card_id: str
    field: str
    new_text: str

class HideOp(TypedDict):
    type: Literal["hide"]
    card_id: str

class InsertKeywordOp(TypedDict):
    type: Literal["insert_keyword"]
    card_id: str
    keywords: list[str]

Operation = Union[ReorderOp, EmphasizeOp, RewriteOp, HideOp, InsertKeywordOp]

# 3. 求职机会创建
class CreateApplicationIn(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=10000)
    source_url: str | None = None

class ApplicationOut(BaseModel):
    id: UUID
    status: ApplicationStatus
    priority: int
    notes: str
    created_at: datetime
    last_active_at: datetime
    job_posting: JobPostingOut

# 4. 资源创建
class CreateResourceIn(BaseModel):
    type: ResourceType = ResourceType.OTHER
    title: str = Field(..., min_length=1, max_length=256)
    content_text: str = ""
    source_url: str | None = None
    tags: list[str] = []
```

### FastAPI 路由示例（资源生成补丁分支）

```python
@router.post("", response_model=BranchDetail, status_code=201)
async def create_branch(
    app_id: UUID,
    body: CreateBranchIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BranchDetail:
    """
    为指定求职机会生成新简历补丁分支。

    流程：
    1. 拉主简历 + JD
    2. AI 生成 PatchOperations + 修改理由（启用 Prompt Caching）
    3. apply_operations 渲染当前版本（含 30% 改写硬约束）
    4. AI 评分
    5. 旧分支 is_active=False，新分支 is_active=True
    """
    app = _get_app(app_id, user, db)
    r = _get_master(user, db)
    master = _serialize_master(r)
    jd = _serialize_jd(app)
    lang = body.language or jd.get("language", "zh")

    out = await generate_patch(master, jd, lang, user.id)
    try:
        rendered = apply_operations(master, out["patch"])
    except RewriteTooLargeError as e:
        raise HTTPException(422, str(e))

    score = await score_branch(rendered, jd, user.id)
    _deactivate_other_branches(db, app_id)

    b = ResumeBranch(
        application_id=app_id,
        version_label=_next_version(db, app_id),
        patch=out["patch"],
        ai_reasoning=out["reasoning"],
        match_score=score,
        language=lang,
        is_active=True,
    )
    db.add(b); db.commit(); db.refresh(b)
    return BranchDetail(
        id=b.id, version_label=b.version_label, match_score=b.match_score,
        language=b.language, created_at=b.created_at, is_active=b.is_active,
        patch=b.patch, ai_reasoning=b.ai_reasoning,
        rendered_resume=rendered, master_snapshot=master,
    )
```

---

## 5. AI 模型集成方案

### LLMClient 统一抽象层

```python
from time import perf_counter
from uuid import UUID
from litellm import acompletion
from litellm.cost_calculator import completion_cost
from src.core.db import SessionLocal
from src.models.ai_call_log import AICallLog

FALLBACK_CHAIN = {
    # v1 单供应商 MiniMax；同家族两档兜底
    "auto-m1": [
        "minimax/MiniMax-M1",
        "minimax/abab6.5s-chat",
    ],
    "auto-light": [
        "minimax/abab6.5s-chat",
    ],
}

class LLMClient:
    """统一 LLM 调用入口。自动两档兜底 + 自动写 ai_call_logs。"""

    async def acomplete(
        self,
        model: str,                # "auto-m1" / "auto-light" / 具体模型名
        system: str,
        messages: list[dict],
        max_tokens: int = 1024,
        user_id: UUID | None = None,
        scene: str = "unknown",
    ) -> str:
        full = [{"role": "system", "content": system}, *messages]
        chain = FALLBACK_CHAIN.get(model, [model])
        last_exc = None
        for m in chain:
            t0 = perf_counter()
            try:
                resp = await acompletion(model=m, messages=full, max_tokens=max_tokens)
                text = resp.choices[0].message.content or ""
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, m, resp, latency, "ok", None)
                return text
            except Exception as e:
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, m, None, latency, "error", str(e)[:500])
                last_exc = e
        raise RuntimeError(f"All MiniMax fallbacks failed: {last_exc}")
```

> **LiteLLM provider 配置（v1 只填 MiniMax）**
> ```yaml
> # litellm_config.yaml
> model_list:
>   - model_name: minimax/MiniMax-M1
>     litellm_params:
>       model: openai/MiniMax-M1            # OpenAI-compatible chat completion
>       api_base: https://api.minimax.chat/v1
>       api_key: os.environ/MINIMAX_API_KEY
>   - model_name: minimax/abab6.5s-chat
>     litellm_params:
>       model: openai/abab6.5s-chat
>       api_base: https://api.minimax.chat/v1
>       api_key: os.environ/MINIMAX_API_KEY
> ```
> 海外节点把 `api_base` 换成 `https://api.minimaxi.chat/v1` 即可；密钥仅一把 `MINIMAX_API_KEY`。

### 9 个 AI 调用场景汇总

| # | 场景（scene） | 模型 | 单次成本（¥） | 频次 | 用 Context Caching | 触发位置 |
|---|---|---|---|---|---|---|
| 1 | `resume_parse` | auto-m1 | ~¥0.10 | 每用户 1-3 次 | 否 | 上传后解析 |
| 2 | `resume_diagnose` | auto-m1 | ~¥0.04 | 每用户 1-3 次 | 否 | 含金量诊断 |
| 3 | `intake_dialogue` | auto-light | ~¥0.001 | 应届生 5-8 轮 | 否 | 轻问诊每轮 |
| 4 | `intake_finalize` | auto-m1 | ~¥0.06 | 应届生 1 次 | 否 | 轻问诊完成 |
| 5 | `jd_parse` | auto-light | ~¥0.004 | 每 JD 1 次 | 否 | 新增机会 |
| 6 | `patch_generate` | auto-m1 | ~¥0.12（首次）/ ~¥0.04（缓存命中） | 每机会 1-3 次 | **是**（master 部分） | 生成补丁分支 |
| 7 | `resume_score` | auto-light | ~¥0.002 | 每分支 1 次 | 否 | 补丁生成后 |
| 8 | `resource_summarize` | auto-light | ~¥0.003 | 每资源 1 次 | 否 | 创建/更新资源 |
| 9 | `weekly_observation` | auto-m1 | ~¥0.06 | 每周 1 次 | 否 | 本周复盘 |

### MiniMax Context Caching 实现（场景 6）

```python
# patch_generator.py 关键片段
# MiniMax Context Caching 通过 extra_body 传 cache_id 实现：
# 1) 首次调用，把 master_serialized 放入 prompt 前缀，调用返回的 X-Cache-Id 取出存 Redis（key=user_id, TTL=5min）
# 2) 后续 5 分钟内为同一用户的其它 JD 生成补丁，传 cache_id，则 master 部分按缓存计费（约原价 1/3）

cache_id = await _cache_store.get(user_id)  # 5 分钟内的 master 缓存 id

msg_user = {
    "role": "user",
    "content": json.dumps(
        {"master": master_serialized, "jd": jd_serialized, "output_language": language},
        ensure_ascii=False,
    ),
}

raw, new_cache_id = await _llm.acomplete(
    model="auto-m1",
    system=PATCH_GEN_SYSTEM,
    messages=[msg_user],
    user_id=user_id,
    scene="patch_generate",
    extra_body={"cache_id": cache_id} if cache_id else None,  # MiniMax 专用
)
if new_cache_id and not cache_id:
    await _cache_store.set(user_id, new_cache_id, ttl_sec=300)
```

效果：同一用户在 5 分钟内连续为多个 JD 生成补丁，主简历部分按缓存价计费，2 ~ N 次调用的 master 部分输入 token 成本仅为首次的 ~33%；整体补丁生成成本从 ¥0.12 降到 ¥0.04 左右。

### 单用户月成本估算（MiniMax 单价）

```
活跃用户典型场景（社招跳槽）：
  - 1 次 上传 + 解析 + 诊断           : ¥0.14
  - 10 个 JD × 平均 2 版补丁         : ¥0.12 × 20 = ¥2.40
    └─ MiniMax Context Caching 后 ≈ : ¥0.80
  - 10 次 JD 解析                    : ¥0.04
  - 10 次 评分                       : ¥0.02
  - 20 次 资源摘要                   : ¥0.06
  - 4 次 本周观察                    : ¥0.24
  ─────────────────────────────────
  合计（缓存后）≈ ¥1.30 / 月（约 $0.19 USD）
```

### 三级成本控制开关

1. **单用户日成本上限**：`MAX_COST_PER_USER_PER_DAY = ¥35`（约 $5），触达后该用户当日剩余 AI 请求自动降级到 abab6.5s
2. **总成本日上限**：`MAX_COST_TOTAL_PER_DAY = ¥1400`（约 $200），触达后全局降级 + 短信告警
3. **红线熔断**：`MAX_COST_TOTAL_PER_DAY × 2`，触达后全局 AI 临时停用（返回友好提示），人工 review

实现：每次 `LLMClient.acomplete` 调用前查 Redis 计数器（O(1)），异常路径走 abab6.5s 兜底。

---

## 6. 性能优化方案

### 数据库层
- **关键索引**：
  - `users(email_lookup_hash)` UNIQUE
  - `users(wechat_openid)` UNIQUE
  - `applications(user_id, status, last_active_at DESC)` 复合
  - `resume_branches(application_id, created_at DESC)`
  - `ai_call_logs(user_id, created_at)` 用于成本仪表盘
  - `weekly_digests(user_id, week_of)` UNIQUE
- **连接池**：SQLAlchemy `pool_pre_ping=True`，pool_size=10，max_overflow=20
- **关联预加载**：`selectinload(Application.job_posting)`，避免 N+1
- **PatchOperations 设计**：补丁存操作而非全文本，单分支记录从 5-10 KB 降到 200-500 B

### AI 调用层
- **MiniMax Context Caching**：主简历序列化作为缓存前缀，命中后缓存部分价格约为原价 1/3，整体补丁生成成本降 ~70%（详 §5）
- **小模型先筛**：JD 解析、资源摘要、评分等用 abab6.5s-chat（成本 ≈ MiniMax-M1 的 1/6）
- **结果落库不重跑**：所有 AI 输出存数据库，刷新页面或重复查看不重复调用
- **Streaming 暂不做**：v1 同步返回，避免 SSE 复杂度（v1.5 评估）
- **并发限制**：单用户 RPM = 60，防止恶意刷

### 前端层
- **TanStack Query staleTime 30s**：列表数据不频繁刷
- **路由级 prefetch**：Next.js Link 自动预取目标页面
- **图片优化**：Next.js `<Image>` 自动 WebP + 响应式
- **代码分割**：App Router 自动按路由切分 bundle
- **SVG 图表替代 Chart 库**：内部 Dashboard 用纯 SVG（节省 ~150KB）

### 文件处理
- **浏览器直传 S3**：用 PUT 预签名 URL，简历文件不经后端，减带宽
- **PDF 解析降级**：复杂版式 PDF 抽取失败时回退到 OCR（v1.5 上）
- **WeasyPrint 字体缓存**：进程内复用 FontConfiguration

### CI 与构建
- **e2e 仅冒烟**：关键路径 4-6 测试，不跑全量
- **依赖锁定 + 缓存**：pnpm-lock.yaml + pip wheel cache，CI < 5 分钟
- **并行 job**：web 与 api 在 GitHub Actions 并行跑

---

## 7. 项目配置

### 仓库结构（pnpm Monorepo）

```
job-companion/
├── apps/
│   ├── web/                              # Next.js 15 前端
│   │   ├── src/
│   │   │   ├── app/[locale]/             # i18n 路由
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx              # 首页
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/page.tsx
│   │   │   │   │   └── verify/page.tsx
│   │   │   │   └── (app)/
│   │   │   │       ├── layout.tsx        # 全局 5-入口侧栏
│   │   │   │       ├── dashboard/page.tsx
│   │   │   │       ├── onboarding/page.tsx
│   │   │   │       ├── opportunities/
│   │   │   │       │   ├── page.tsx
│   │   │   │       │   └── [id]/
│   │   │   │       │       ├── layout.tsx     # 5 列 Tab 壳
│   │   │   │       │       ├── resume/page.tsx
│   │   │   │       │       └── investments/page.tsx
│   │   │   │       ├── master-resume/page.tsx
│   │   │   │       ├── resources/page.tsx
│   │   │   │       ├── weekly/page.tsx
│   │   │   │       └── coach/page.tsx
│   │   │   ├── app/internal/dashboard/   # 内部 Dashboard（不走 i18n）
│   │   │   │   └── page.tsx
│   │   │   ├── components/
│   │   │   │   ├── auth/                 # MagicLinkForm / WeChatQR / PersonaPicker
│   │   │   │   ├── nav/                  # SideNav / LocaleSwitcher
│   │   │   │   ├── disguise/             # 伪装界面
│   │   │   │   ├── master-resume/        # 卡片编辑器
│   │   │   │   ├── opportunities/        # OpportunityCard / NewOpportunityDialog
│   │   │   │   ├── resume/               # ResumeWorkspace / DiffView / ExportDialog
│   │   │   │   ├── resources/            # ResourceCard / CollectionSidebar
│   │   │   │   ├── investment/           # InvestmentTimeline
│   │   │   │   ├── weekly/               # StatGrid / ObservationCard
│   │   │   │   ├── coach/                # CoachInquiryDrawer
│   │   │   │   ├── common/               # CapacityGate
│   │   │   │   └── internal/             # StatCards / SimpleChart
│   │   │   ├── hooks/                    # TanStack Query hooks
│   │   │   ├── lib/                      # api / posthog / queryClient
│   │   │   └── i18n/request.ts
│   │   ├── messages/{zh,en}.json
│   │   ├── middleware.ts                 # next-intl + locale 路由
│   │   ├── e2e/                          # Playwright 测试
│   │   ├── playwright.config.ts
│   │   ├── vitest.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── next.config.mjs
│   │   └── package.json
│   └── api/                              # FastAPI 后端
│       ├── src/
│       │   ├── main.py
│       │   ├── core/
│       │   │   ├── config.py             # pydantic-settings
│       │   │   ├── db.py                 # engine + SessionLocal
│       │   │   ├── security.py           # encrypt / JWT
│       │   │   ├── deps.py               # current_user
│       │   │   ├── internal_auth.py      # 内部 dashboard 密码
│       │   │   └── analytics.py          # PostHog server-side
│       │   ├── models/                   # SQLAlchemy ORM
│       │   │   ├── user.py
│       │   │   ├── master_resume.py
│       │   │   ├── cards.py
│       │   │   ├── application.py
│       │   │   ├── job_posting.py
│       │   │   ├── resume_branch.py
│       │   │   ├── resource_item.py
│       │   │   ├── resource_collection.py
│       │   │   ├── investment.py
│       │   │   ├── intake_session.py
│       │   │   ├── weekly_digest.py
│       │   │   ├── coach_inquiry.py
│       │   │   ├── ai_call_log.py
│       │   │   ├── magic_link_token.py
│       │   │   └── application_resource_link.py
│       │   ├── schemas/                  # Pydantic
│       │   ├── routers/
│       │   │   ├── health.py
│       │   │   ├── auth.py
│       │   │   ├── me.py
│       │   │   ├── master_resume.py
│       │   │   ├── application.py
│       │   │   ├── resume_branch.py
│       │   │   ├── investment.py
│       │   │   ├── resource.py
│       │   │   ├── weekly.py
│       │   │   ├── coach.py
│       │   │   └── internal_dashboard.py
│       │   ├── services/
│       │   │   ├── storage.py            # S3 预签名
│       │   │   ├── text_extractor.py     # PDF/Docx
│       │   │   ├── resume_parser.py      # AI 简历解析
│       │   │   ├── quality_diagnoser.py
│       │   │   ├── intake.py             # 应届轻问诊
│       │   │   ├── jd_parser.py
│       │   │   ├── patch_generator.py    # AI 补丁生成（含 caching）
│       │   │   ├── patch_ops.py          # PatchOps DSL + apply
│       │   │   ├── resume_scorer.py
│       │   │   ├── template_renderer.py  # Jinja2
│       │   │   ├── pdf_renderer.py       # WeasyPrint
│       │   │   ├── resource_processor.py
│       │   │   ├── weekly_stats.py
│       │   │   ├── weekly_observer.py
│       │   │   ├── weekly_digester.py
│       │   │   ├── notifier.py           # 飞书 / Telegram / 邮件
│       │   │   ├── email_sender.py
│       │   │   ├── magic_link.py
│       │   │   ├── wechat.py
│       │   │   └── time_helpers.py       # 北京时区周计算
│       │   ├── ai/
│       │   │   ├── llm_client.py         # LLMClient 抽象
│       │   │   └── prompts/              # 所有 system prompts
│       │   ├── templates/resume/
│       │   │   ├── base.css
│       │   │   ├── zh_simple.html
│       │   │   └── en_simple.html
│       │   └── jobs/
│       │       └── scheduler.py          # APScheduler
│       ├── alembic/
│       │   ├── env.py
│       │   └── versions/
│       │       ├── 0001_initial.py       # users
│       │       ├── 0002_magic_link_tokens.py
│       │       ├── 0003_ai_call_log.py
│       │       ├── 0004_master_resume_and_cards.py
│       │       ├── 0005_intake_session.py
│       │       ├── 0006_application_jobposting.py
│       │       ├── 0007_application_resource_link.py
│       │       ├── 0008_resume_branch.py
│       │       ├── 0009_resources.py
│       │       ├── 0010_investment.py
│       │       ├── 0011_weekly_digest.py
│       │       └── 0012_coach_inquiry.py
│       ├── tests/
│       │   ├── conftest.py
│       │   └── test_*.py
│       ├── pyproject.toml
│       ├── alembic.ini
│       └── Dockerfile
├── packages/
│   └── shared-types/
│       ├── events.ts                     # PostHog 事件枚举（强类型）
│       └── package.json
├── infra/
│   ├── docker-compose.yml                # 本地 postgres + redis + api + web
│   └── deploy/
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   ├── 2026-06-27-job-companion-design.md
│       │   └── 2026-06-27-job-companion-PRD.md
│       └── plans/
│           ├── 2026-06-27-job-companion-v1-overview.md
│           └── 2026-06-27-plan-0..7-*.md
├── .github/workflows/ci.yml
├── pnpm-workspace.yaml
├── package.json
├── .gitignore
├── .editorconfig
├── .nvmrc
└── README.md
```

### 环境变量清单

`apps/api/.env.example`：

```bash
# === 基础 ===
APP_ENV=development                                # development / test / production
DATABASE_URL=postgresql+psycopg://jc:jc_dev@postgres:5432/jc_dev
REDIS_URL=redis://redis:6379/0

# === 鉴权 ===
JWT_SECRET=                                         # 32+ 字节随机
JWT_ALG=HS256
JWT_EXPIRES_HOURS=720                              # 30 天
FIELD_ENCRYPTION_KEY=                              # Fernet key (base64-urlsafe 32 bytes)

# === 微信登录 ===
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=https://app.example.com/api/auth/wechat/callback

# === 邮件 ===
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

# === LLM ===
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=

# === S3 ===
S3_BUCKET=job-companion-prod
S3_REGION=auto
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=

# === 监控 ===
SENTRY_DSN=
POSTHOG_API_KEY=
POSTHOG_HOST=https://us.i.posthog.com

# === 通知 ===
NOTIFIER_TYPE=feishu                               # print / feishu / telegram / email
FEISHU_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# === 内部 Dashboard ===
INTERNAL_DASHBOARD_PASSWORD=                       # 强密码
```

`apps/web/.env.example`：

```bash
NEXT_PUBLIC_API_BASE=https://api.example.com
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
NEXT_PUBLIC_SENTRY_DSN=
```

### Docker Compose（本地开发）

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: jc
      POSTGRES_PASSWORD: jc_dev
      POSTGRES_DB: jc_dev
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jc -d jc_dev"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: { context: ../apps/api, dockerfile: Dockerfile }
    depends_on: { postgres: { condition: service_healthy } }
    env_file: ../apps/api/.env
    ports: ["8000:8000"]
    volumes: ["../apps/api:/app"]
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --app-dir .

  web:
    build: { context: ../apps/web, dockerfile: Dockerfile }
    depends_on: [api]
    env_file: ../apps/web/.env
    ports: ["3000:3000"]
    volumes:
      - ../apps/web:/app
      - /app/node_modules
      - /app/.next
    command: pnpm dev

volumes:
  pgdata:
```

### CI / GitHub Actions

```yaml
name: ci
on:
  pull_request:
  push: { branches: [main] }

jobs:
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile=false
      - run: pnpm --filter web lint
      - run: pnpm --filter web typecheck
      - run: pnpm --filter web test
      - run: pnpm --filter web exec playwright install --with-deps chromium
      - run: pnpm --filter web e2e

  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_USER: jc, POSTGRES_PASSWORD: jc_dev, POSTGRES_DB: jc_dev }
        ports: ['5432:5432']
        options: --health-cmd="pg_isready -U jc" --health-interval=5s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - working-directory: apps/api
        run: pip install -e ".[dev]"
      - working-directory: apps/api
        env:
          DATABASE_URL: postgresql+psycopg://jc:jc_dev@localhost:5432/jc_dev
          JWT_SECRET: ci-test-secret-32bytes-min-padding
          FIELD_ENCRYPTION_KEY: ${{ secrets.FIELD_ENCRYPTION_KEY }}
          APP_ENV: test
        run: |
          alembic upgrade head
          ruff check src tests
          mypy src
          pytest -q
```

---

## 8. 国际化（i18n）技术方案

### 框架选型
[next-intl 3.25](https://next-intl-docs.vercel.app/) — Next.js 15 + App Router 官方推荐的 i18n 方案。

### 路由策略
- **前缀模式**：`/zh/*` 和 `/en/*`，所有页面都带 locale 前缀
- **默认语言**：`zh`（访问 `/` 自动 302 到 `/zh`）
- **中间件**：`middleware.ts` 自动检测 + 重定向 + 排除 `/api`、`/_next`、`/internal`

```typescript
// middleware.ts
import createMiddleware from 'next-intl/middleware'
export default createMiddleware({
  locales: ['zh', 'en'],
  defaultLocale: 'zh',
  localePrefix: 'always',
})
export const config = {
  matcher: ['/((?!api|_next|internal|.*\\..*).*)'],
}
```

### 翻译文件组织

按模块 namespace 组织，文件 `messages/zh.json` 与 `messages/en.json`：

```json
{
  "home": { "title": "...", "tagline": "..." },
  "nav": { "opportunities": "...", "master_resume": "...", "resources": "...", "weekly": "...", "coach": "..." },
  "auth": { "login": "...", "email_label": "...", "send_magic_link": "...", "wechat_scan": "..." },
  "master_resume": { ... },
  "opportunities": { ... },
  "resume_tab": { ... },
  "investments": { ... },
  "resources": { ... },
  "weekly": { ... },
  "coach": { ... }
}
```

### 使用模式

**服务端组件**：
```typescript
import { useTranslations } from 'next-intl'
export default function Page() {
  const t = useTranslations('home')
  return <h1>{t('title')}</h1>
}
```

**客户端组件**（带变量插值）：
```typescript
'use client'
import { useTranslations } from 'next-intl'
export function CoachAvailability({ remaining }: { remaining: number }) {
  const t = useTranslations('coach')
  return <p>{t('slots_open', { n: remaining })}</p>
}
```

**带 locale 切换**：
```typescript
'use client'
import { useParams, useRouter, usePathname } from 'next/navigation'
export function LocaleSwitcher() {
  const { locale } = useParams<{ locale: string }>()
  const router = useRouter()
  const path = usePathname()
  const other = locale === 'zh' ? 'en' : 'zh'
  return <button onClick={() => router.push(path.replace(`/${locale}`, `/${other}`))}>{other === 'zh' ? '中' : 'EN'}</button>
}
```

### 后端 AI 输出语言跟随

```python
# JD 自动检测语言
class JobPosting:
    language: str   # "zh" or "en"，AI 解析时判定（中文字符 > 50% → zh）

# 补丁生成时传入
async def generate_patch(master, jd, language, user_id):
    user_payload = {"master": master, "jd": jd, "output_language": language}
    # ...

# PDF 模板按语言选择
def render_html(rendered, language, mask_current_company):
    tpl = _env.get_template("zh_simple.html" if language == "zh" else "en_simple.html")
    # ...
```

### 简历模板

- `apps/api/src/templates/resume/zh_simple.html`：中文简洁模板
- `apps/api/src/templates/resume/en_simple.html`：英文简洁模板
- 共用 `base.css`：中文字体 fallback `Noto Sans CJK SC → Noto Sans`，英文 `Helvetica → Inter → Arial`
- 现公司脱敏 label：`{"zh": "某知名互联网公司", "en": "Major Tech Company"}`

### 不在 i18n 范围

- `/internal/dashboard` 仅英文（PM 自用）
- API 响应不做 i18n（错误码 + code，前端按 locale 渲染文案）
- 邮件模板 v1 仅中文（v1.5 加英文）
- PostHog 事件名固定英文 snake_case

---

## 9. 部署架构

### 生产环境拓扑

```
┌──────────────────────────────────────────────────────────────┐
│                     用户（中国 / 海外）                       │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Vercel Edge CDN    │   │  api.example.com    │
│  app.example.com    │   │  (Fly.io / 阿里 ECS)│
│  Next.js 15         │   │  FastAPI + Uvicorn  │
│  (SSR + RSC + CDN)  │   │  Docker 容器化       │
└─────────────────────┘   └──────────┬──────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
                  ▼                  ▼                  ▼
        ┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
        │ Supabase Postgres│ │ Upstash Redis│ │ Cloudflare R2   │
        │ 自动备份 + PITR  │ │ Serverless   │ │ S3 兼容存储     │
        └──────────────────┘ └──────────────┘ └─────────────────┘
                  ▲
                  │
                  ├──── Sentry SaaS（异常）
                  ├──── PostHog Cloud（行为）
                  ├──── MiniMax API（M1 + abab6.5s；国内 api.minimax.chat / 海外 api.minimaxi.chat）
                  └──── 飞书 webhook（PM 通知）
```

### 环境分离

| 环境 | 域名 | DB | 用途 |
|---|---|---|---|
| dev | localhost:3000 / :8000 | docker postgres | 本地开发 |
| preview | `*.vercel.app` | Supabase preview branch | PR 自动预览 |
| staging | staging.example.com | Supabase staging | 上线前验收 |
| production | app.example.com | Supabase production | 正式 |

### 数据备份

- Supabase 自动每日 backup（保留 7 天）+ Point-in-time recovery
- Cloudflare R2 启用版本控制 + 删除保护
- 每周一手工触发一次完整备份导出到独立账号（防 Supabase 账户级故障）

### 回滚策略

- Vercel：保留近 10 个 deployment，一键回滚
- Fly.io：`fly releases list` + `fly releases rollback`
- 数据迁移：Alembic 每个 migration 必须实现 `downgrade()`；上线前在 staging 演练

### 大陆访问考虑

- **方案 A（推荐）**：海外用户直连 + 大陆用户通过 CDN 加速；后端按部署区域选择 MiniMax endpoint（大陆 `api.minimax.chat`、海外 `api.minimaxi.chat`）
- **方案 B**：双节点部署（Fly.io 海外 + 阿里 ECS 大陆），DNS 智能解析；两侧分别配自己的 MiniMax endpoint

v1 默认走方案 A，监控大陆 P95 延迟，超过 2s 切方案 B。MiniMax 同时拥有国内外可达的 API endpoint，本地化访问问题相对可控。

---

## 10. 安全与隐私

### 传输安全
- 全链路 HTTPS（Vercel 自动 + Fly.io 自动）
- HSTS Header（生产开 1 年）
- CSP（v1.5 上）

### 鉴权安全
- JWT HS256，secret 32 字节随机
- Cookie 配置：`HttpOnly + Secure + SameSite=Lax + Max-Age=30d`
- 关键操作（删账号、修改密码）v1.5 加二次验证

### 数据安全
- **字段级加密**（Fernet）：邮箱、电话、`current_company`
- **email_lookup_hash**：sha256，唯一查询用
- **预签名 URL**：上传 10 分钟，下载 24 小时；导出 PDF 单链接 7 天
- **S3 SSE-S3**：对象存储服务端加密
- **审计日志**：所有 PII 字段访问（解密调用）记录到独立日志（v1.5 上）

### 输入安全
- 所有 endpoint Pydantic 严格校验，禁 `Any` 出现在签名
- SQL 注入：SQLAlchemy ORM 全参数化，禁手拼 SQL
- XSS：Next.js 默认转义；危险的富文本场景用 DOMPurify
- 文件上传：MIME + 扩展名双重校验，最大 10 MB

### 隐私保护
- **现公司脱敏**：导出 PDF 默认 ON（替换为「某知名互联网公司」/「Major Tech Company」）
- **伪装界面**：Ctrl+\` 全局快捷键，秒切番茄钟+待办 + tab 标题/favicon 同步切
- **不主动分享**：v1 不提供"分享我的简历到朋友圈"等导出社交化功能
- **GDPR 友好**：所有用户数据可一键导出 + 删账号物理清除（v1.5 上）

### 危险操作防护
- 删除资源 / 删除分支 / 删合集 / 归档机会等可逆操作 → 前端二次确认
- AI 改写超 30% 字数 → 后端 422 拒绝
- 现公司经历卡 UI 上有醒目"🔒 这是你现在的公司，导出时默认脱敏"提示

### 内部 Dashboard 保护
- 独立路由前缀 `/internal/`，i18n 中间件不处理
- `X-Internal-Password` Header + env 比对
- 密码缓存在 sessionStorage（关浏览器即失效）

---

## 11. 测试与质量

### 测试金字塔

```
                     ┌─────────────┐
                     │ Playwright  │  关键路径冒烟（4-6 测试）
                     │   e2e       │
                     └─────────────┘
                  ┌──────────────────┐
                  │  接口测试         │  TestClient + 真实 Postgres（覆盖每个 router）
                  │  (TestClient)    │
                  └──────────────────┘
            ┌──────────────────────────────┐
            │       单元测试                │  pytest / vitest（覆盖 service + 工具函数）
            │  (pytest / vitest)           │
            └──────────────────────────────┘
```

### AI Mock 策略

CI 不调真实 LLM。所有 AI service 测试统一：

```python
from unittest.mock import patch, AsyncMock
import json

@pytest.mark.asyncio
async def test_parse_returns_pydantic():
    fake = {"basic_info": {"name": "张三"}, "ability_cards": [], "project_cards": [], "experience_cards": []}
    with patch("src.services.resume_parser._llm.acomplete",
               AsyncMock(return_value=json.dumps(fake))):
        out = await parse_resume_text("any text", PersonaType.JOB_HOPPER, uuid4())
    assert out.basic_info["name"] == "张三"
```

### DB Fixture（pytest）

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def engine():
    e = create_engine(get_settings().database_url, future=True)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)

@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()
```

### 测试覆盖矩阵

| 模块 | 单元 | 接口 | e2e |
|---|---|---|---|
| PatchOps DSL（5 op + 30% guard） | ✅ | — | — |
| LLMClient + ai_call_log 打点 | ✅ | — | — |
| Auth（Magic Link + WeChat + JWT） | ✅ | ✅ | smoke |
| MasterResume CRUD + 解析 | — | ✅ | smoke |
| Application + JD parse + 容量门 | — | ✅ | smoke |
| ResumeBranch + 补丁 + 导出 + 回滚 | — | ✅ | smoke |
| Resources + Collections | — | ✅ | smoke |
| Investments | — | ✅ | — |
| WeeklyDigest（时区 + 统计） | ✅ | ✅ | smoke |
| Coach + Notifier + capacity | — | ✅ | smoke |
| Internal Dashboard（password） | ✅ | ✅ | gate |

### 代码质量约束（CI 必过）

- TypeScript：`tsc --noEmit` 0 error，strict mode 全开
- Python：`mypy --strict src` 0 error，`ruff check src tests` clean
- ESLint：Next.js 默认规则 + 自定义（禁止硬编码用户文案）

---

## 12. 监控与运维

### Sentry（异常）
- 前端：`@sentry/nextjs`，自动捕获未处理 Promise + React 错误边界
- 后端：`sentry-sdk[fastapi]`，自动捕获 500 + middleware 集成
- `traces_sample_rate=0.1`（10% 采样以控制成本）

### PostHog（行为）
- 强类型事件枚举：`packages/shared-types/events.ts`
- v1 事件清单：

```typescript
export const Events = {
  // Auth
  USER_SIGNED_IN: 'user_signed_in',
  USER_PERSONA_PICKED: 'user_persona_picked',

  // UX
  DISGUISE_TOGGLED: 'disguise_toggled',
  LOCALE_SWITCHED: 'locale_switched',
  AI_HEALTH_CHECKED: 'ai_health_checked',

  // MasterResume
  MASTER_RESUME_UPLOAD_STARTED: 'master_resume_upload_started',
  MASTER_RESUME_PARSED: 'master_resume_parsed',
  MASTER_RESUME_DIAGNOSED: 'master_resume_diagnosed',
  INTAKE_STARTED: 'intake_started',
  INTAKE_FINALIZED: 'intake_finalized',

  // Opportunity
  OPPORTUNITY_CREATED: 'opportunity_created',
  OPPORTUNITY_OPENED: 'opportunity_opened',
  OPPORTUNITY_ARCHIVED: 'opportunity_archived',

  // Resume Branch
  RESUME_BRANCH_GENERATED: 'resume_branch_generated',
  RESUME_BRANCH_EXPORTED: 'resume_branch_exported',
  RESUME_BRANCH_ROLLBACK: 'resume_branch_rollback',
  RESUME_MODE_SWITCHED: 'resume_mode_switched',

  // Resources
  RESOURCE_CREATED: 'resource_created',
  RESOURCE_DELETED: 'resource_deleted',
  COLLECTION_CREATED: 'collection_created',
  RESOURCE_LINKED_TO_APP: 'resource_linked_to_app',

  // Investments
  INVESTMENT_CREATED: 'investment_created',
  INVESTMENT_DELETED: 'investment_deleted',

  // Weekly
  WEEKLY_OPENED: 'weekly_opened',
  WEEKLY_REFRESHED: 'weekly_refreshed',
  WEEKLY_ACTION_CLICKED: 'weekly_action_clicked',

  // Coach
  COACH_INQUIRY_OPENED: 'coach_inquiry_opened',
  COACH_INQUIRY_SUBMITTED: 'coach_inquiry_submitted',
  COACH_AVAILABILITY_VIEWED: 'coach_availability_viewed',
} as const
```

### 内部成本仪表盘

**4 个 KPI 卡片**：DAU / MAU / Total Users / Coach 本周
**4 个 AI 成本卡片**：今日调用 / 今日成本 / 30 日调用 / 30 日成本
**3 张 SVG 折线图**（30 天）：DAU / AI calls per day / AI cost per day

```
GET /internal/dashboard/summary    → 8 个 KPI
GET /internal/dashboard/timeseries → 30 个日聚合数据点
```

### 告警规则

| 阈值 | 告警方式 |
|---|---|
| 单用户日 AI 成本 > ¥35（≈$5） | Sentry warning + 该用户当日降级到 abab6.5s |
| 总日 AI 成本 > ¥1400（≈$200） | 短信 PM + 全局降级到 abab6.5s |
| 总日 AI 成本 > ¥2800（≈$400） | 短信 PM + 全局熔断（停 AI） |
| API 5xx 率 > 1% | Sentry alert |
| Coach 申请 24h 内 PM 未触达 | 飞书 ping（v1.5） |

### 日志策略

- 应用日志：stdout（Vercel / Fly.io 自动收集 + 保留 7 天）
- 敏感字段（email、phone、wechat_openid）禁出现在日志中
- 关键操作 trace ID（v1.5）

### Cron 任务

| 任务 | 频率 | 实现 |
|---|---|---|
| Weekly Digest 预生成 | 每周一 00:30 BJT | APScheduler in-process |
| 过期 magic_link_tokens 清理 | 每日 02:00 | v1.5 加 |
| S3 残留文件清理 | 每周日 03:00 | v1.5 加 |

---

## 13. 实施路线图

按 8 个 plan 顺序执行：

| Plan | 模块 | 估时 | 关键产出 |
|---|---|---|---|
| 0 | 基础设施 + 项目骨架 | 2-3 周 | Monorepo / Auth / i18n / 伪装界面 / CI / Sentry / PostHog / Playwright |
| 1 | MasterResume | 3 周 | 上传/解析/卡片 CRUD/含金量/应届轻问诊 |
| 2 | Application + JobPosting | 2 周 | 求职机会列表 + JD 解析 + 5 列 Tab 壳 |
| 3 | ResumeBranch + PatchOps | 3-4 周 | 补丁 DSL + diff 双视图 + 中英 PDF |
| 4 | Resources + Collections | 2 周 | 资源库 + 合集 + AI 摘要 |
| 5 | Investments | 1 周 | 投递记录 Tab |
| 6 | Weekly Digest | 1.5 周 | 本周复盘 + AI 观察 + Cron |
| 7 | Coach + 内部 Dashboard | 1.5 周 | 导流表单 + 成本仪表盘 |
| **合计** | | **16-18 周** | **81 task / 350+ bite-sized step** |

详细 task 拆分见 `docs/superpowers/plans/2026-06-27-plan-0..7-*.md`。

---

## 14. 已知技术风险

| # | 风险 | 缓解措施 |
|---|---|---|
| 1 | AI 解析质量差，卡片错乱 | 手动校对/补全 UI + AI 自标"低置信" |
| 2 | 补丁过度优化，简历失真 | 单字段改写 ≤ 30% hard guard + 每条理由 + 一键回滚 |
| 3 | 隐私事故 | Fernet 加密 + 预签名 URL 24h + is_current 强提示 + 默认脱敏 + 审计日志 |
| 4 | MiniMax 单点依赖 | LiteLLM + M1→abab6.5s 同家族两档兜底；双 endpoint（国内/海外）+ 自动重试；如未来需多供应商扩 provider 配置即可 |
| 5 | JD 抓取合规 | v1 仅手动粘贴，链接抓取留 v1.5 + robots 提示 |
| 6 | AI 成本失控 | 三级开关 + 日上限 + 短信告警 + 自动降级 |
| 7 | Coach 服务瓶颈 | 周 5 slot + 售罄 UI + 邮件候补订阅 |
| 8 | WeasyPrint 字体兼容 | 思源 CJK + Inter 双 fallback；CI 装系统字体 |
| 9 | Postgres → Supabase 迁移 | Alembic 全 downgrade 必实现 + staging 演练 |
| 10 | 单元测试覆盖率不足 | CI 加 `pytest --cov`（v1.5 设阈值 70%） |

---

## 15. v1 → v1.5 → v2/v3 演进

| 维度 | v1 | v1.5 | v2 | v3 |
|---|---|---|---|---|
| 简历模板 | 中英各 1 简洁版 | 多模板 | 模板市场 | — |
| 英文措辞地道度评分 | — | ✅ | — | — |
| 转行深度跨域映射 | 接口预留 | ✅ | — | — |
| JD 链接抓取 | — | ✅ | — | — |
| 浏览器插件 | — | ✅ | — | — |
| 多 Agent 锐评 | — | — | ✅（付费墙） | — |
| 面试准备模块（5 列 #3） | — | — | ✅ | — |
| 面试复盘模块（#4） | — | — | — | ✅ |
| Offer 评估模块（#5） | — | — | — | ✅ |
| 小程序 | — | — | — | ✅ |
| ToB（学校/企业版） | — | — | — | ✅ |

---

## 附录：核心接口签名速查

```python
# AI 抽象层
class LLMClient:
    async def acomplete(
        self, model: str, system: str, messages: list[dict],
        max_tokens: int = 1024, user_id: UUID | None = None, scene: str = "unknown",
    ) -> str: ...

# PatchOps 核心
def apply_operations(master: dict, ops: list[dict]) -> dict: ...
def validate_rewrite_intensity(original: str, new: str, max_pct: float = 0.30) -> bool: ...
class RewriteTooLargeError(ValueError): ...

# 存储
def presign_put(key: str, content_type: str, expires_in: int = 600) -> str: ...
def presign_get(key: str, expires_in: int = 86400) -> str: ...
def download_bytes(key: str) -> bytes: ...

# 文本抽取
def extract_text(filename: str, data: bytes) -> str: ...

# 模板与 PDF
def render_html(rendered: dict, language: str, mask_current_company: bool) -> str: ...
def render_pdf(html: str) -> bytes: ...

# Auth
def issue_session_token(user_id: UUID) -> str: ...
def verify_session_token(token: str) -> UUID | None: ...
def encrypt_field(value: str) -> str: ...
def decrypt_field(value: str) -> str: ...

# 时区辅助
def monday_of(now: datetime | None = None) -> date: ...     # 北京时区
def week_range(monday: date) -> tuple[datetime, datetime]: ...

# 通知
async def notify_pm(message: str) -> None: ...
```

---

**文档结束**。更新维护时与对应的 spec / plans 文件保持同步。
