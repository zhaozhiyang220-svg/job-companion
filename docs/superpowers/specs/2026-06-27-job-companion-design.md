# 求职作战中心 · v1 设计稿

| 字段 | 值 |
|---|---|
| **代号** | Job Companion v1（暂定名：求职作战中心） |
| **设计日期** | 2026-06-27 |
| **撰写方法** | superpowers/brainstorming 流程 · 10 轮澄清 + 3 方案选型 + 6 段设计稿 |
| **资源约束** | 个人独开 / 3-4 月窗口 / 1-2 个服 |
| **方案路线** | **B+** — 简历定制中心（功能皮）+ 求职作战图（数据/导航骨架） |
| **变现** | 免费 + 真人 Coach 锐评导流（v1）；多角色 AI 锐评（v2 付费墙） |

---

## §1 用户画像 + 使用情境

### 三类核心人群（v1 全量支持）

| 人群 | 描述 | v1 特殊处理 |
|---|---|---|
| **应届校招** | 22-24 岁，0 工作经验，校招期 / 实习转正 | 主简历薄/为空时触发 AI 轻问诊；补丁强调"潜力词翻译"（学生用语 → 职场用语） |
| **社招跳槽（核心）** | 26-32 岁，1-5 年经验，年薪 15-50w，在职 | 主路径，无特殊处理 |
| **跨行业转行** | 有完整工作经历但跨行业 | 解析时打标"原行业卡片"；补丁启用"跨域映射"模式 |

### 排除人群

- **低学历蓝领求职**：需求完全不同，不需要精致简历/面试复盘
- **被动找工作 / 佛系求职者**：无付费意愿、无高频使用需求

### 四类高频使用情境

| 情境 | 时间 | 场景 | 用户心声 |
|---|---|---|---|
| 🌃 深夜冲刺 | 23:00-1:00 | 床上/书桌前刷 Boss，遇到心动岗位想立刻投 | "再不投明天就被别人抢了" |
| ☕ 工作日午休 | 12:30-13:30 | 工位/咖啡馆，整理上午刷到的 2-3 个岗位 | "先存起来，晚上回家慢慢改" |
| 🛋 周末复盘 | 周日下午 | 回看本周投了哪些、改了几版、为何没回应 | "我到底走偏了没有，要不要换方向" |
| 🔁 周中随时复盘 | 任意 | 想看本周进展和下一步建议 | "现在我该集中精力做哪件事" |

### 三大产品级约束

1. **隐私敏感度极高** → v1 必须做"伪装界面"（一键切到番茄钟+待办伪装界面）；现公司名导出时默认脱敏
2. **不能消耗用户耐心** → 首次上传到拿到第一份定制简历 ≤ **3 分钟**
3. **不教用户做人** → 不写鸡汤、不强问卷、不"AI 教你怎么求职"，只做"帮你把活干快"

---

## §2 核心用户旅程 + Aha Moment

### 主旋律
> **"3 分钟拿到第一份定制简历，每次新 JD 进来都比上次更省力"**

### 首次主旅程（≤ 3 分钟）

```
①  上传简历 PDF/Word              (10s 上传 + 30s 解析)
        ↓
②  AI 解析为「能力卡 + 项目卡 + 经历卡」结构化主版本
    用户校对/补漏                  (60-90s)
        ↓
③  粘贴 JD 文本/链接 → AI 抓取关键词、隐性偏好、雷区
    生成补丁分支：高亮 diff（左：主版本，右：补丁版）
        ↓
④  一键导出 PDF（中文/英文模板）
```

### 复用旅程（第 2 次起，≤ 90 秒）

```
新增机会（粘 JD）→ AI 用主版本生成补丁 → diff 校对 → 导出
```

### 周中/周末复盘旅程

```
本周复盘 → AI 顶部"本周观察" → 进入薄弱主简历项补强 / 调整下周策略
```

### 三次 Aha Moment

1. **X 光透视**：上传后 30s，AI 把简历结构化拆解 + 标出"含金量低"项 → "我的简历被透视了"
2. **修改理由**：粘 JD 后看到 diff 高亮 + AI 为每条修改给出理由 → "它是赋能我而非替代我"
3. **共同成长**（v1 留好钩子）：第 3-5 个 JD 后，AI 弹"这几个岗位都强调 X，要不要把它从主版本里前置"→ "它在和我一起成长"

### 三人群差异化分支（v1 全做）

| 人群 | 上传时 | 补丁分支时 |
|---|---|---|
| 应届生 | 简历薄时触发"轻问诊"（5-8 个问题挖经历） | 强调潜力词翻译 |
| 社招跳槽 | 主路径 | 主路径 |
| 转行者 | 卡片打标"原行业" + 引导补充通用能力标签 | 启用"跨域映射"翻译 |

---

## §3 信息架构 + 模块划分

### 顶层导航（5 个一级入口 + 增值入口）

```
┌─────────────────────────────────┐
│  💼 求职作战中心                │
├─────────────────────────────────┤
│  🎯 我的求职机会     [12]      │  ← Application 列表
│  📋 我的主简历                  │
│  📚 我的资源库       [38]      │  ← 横向数据层（面经/公司情报）
│  📊 本周复盘         · NEW     │
│                                 │
│  💬 找 Coach 锐评    💎        │  ← 增值导流
│  ⚙️ 设置                        │
│  👤 我的账号                    │
└─────────────────────────────────┘
                          [👁 伪装] [🌐 中/EN]  ← 右上角常驻
```

### 求职机会列表（主入口）

每条机会卡片含：公司 · 岗位 · 部门/薪资 · 上次更新 · 当前简历版本号 + 评分 + 状态标。

### 单机会内部：5 列 Tab（v1 只点亮第一列，其余灰显 + 路线图提示）

```
[📝 简历定制 ✓] [📮 投递记录 v1✓ 轻] [🎤 面试准备 🔒v2] [📋 面试复盘 🔒v3] [💼 Offer 评估 🔒v3]
```

> 注：根据用户决策，**投递记录（investments）v1 做实**——能记录"已投/已读/已约面"等基础动作，但不接通自动追踪。

### 简历定制模块布局（并排双视图为默认）

```
┌────────────────┬──────────────────────────────┐
│ JD 解读        │   简历对比视图（默认并排）   │
│ ─────────      │  ┌──────────┬──────────┐    │
│ • 关键词 ×8    │  │ 主版本    │ 补丁 v3   │    │
│ • 隐性偏好 ×3  │  │ 能力卡    │ 能力卡 ↕  │    │
│ • 雷区提示 ×2  │  │ 项目卡    │ 项目卡 ✏  │    │
│ • 评分 82/100  │  │ 经历卡    │ 经历卡 ─  │    │
│                │  └──────────┴──────────┘    │
│ AI 修改理由 →  │  [diff 高亮 / 并排 / 合并]  │
│                │                              │
│                │  [💾 保存] [📤 导出 PDF]    │
│                │  [💬 找 Coach 锐评] 💎      │
└────────────────┴──────────────────────────────┘
```

### 主简历模块

能力库（标签云）/ 项目库（卡片列表）/ 经历库（时间轴）  ·  AI 标"含金量低 ⚠×3"

### 本周复盘模块

数据统计（新增机会/定制版本/导出/Coach 咨询）+ AI 本周观察 + 建议下一步

### 资源库模块

- 资源类型：面经 / 公司情报 / 招聘者背景 / 行业资料 / 其他
- **资源合集（Collection）**：可分组管理资源
- 多对多关联：一份资源可挂载多个机会和公司
- AI 摘要 + 信号提取，可被简历定制流程自动调取作为上下文

### 伪装界面（关键差异化）

- 触发：右上角按钮 / 全局快捷键（Ctrl+`） / 浏览器标签自动伪装
- **伪装为：番茄钟 + 待办清单**（最合理出现在工位）
- 再次快捷键秒回原状

### 语言切换

- 右上角中英切换按钮
- v1 中英 UI 完整 / 中英简历完整支持

---

## §4 数据模型骨架（B+ 最关键的一节）

### 设计原则

1. 以 **Application（求职机会）为中心**，不以 Resume 为中心
2. 主简历存**原子卡片**，不存大段文本
3. 资源库**横向打通**——一份资源可关联多个机会/公司
4. v1 字段做实，v2/v3 字段留空但保留，避免后期改 schema

### 实体关系图

```
                      ┌─────────────┐
                      │    User     │
                      └──────┬──────┘
              ┌──────────────┼─────────────────────┐
              ▼              ▼                     ▼
      ┌─────────────┐ ┌─────────────┐  ┌──────────────────────┐
      │MasterResume │ │ Application │  │ResourceItem ──────── │
      │   (1:1)     │ │   (1:N)     │  │ ResourceCollection   │
      └──────┬──────┘ └──────┬──────┘  └──────┬───────────────┘
             │               │                │
             │               │                │ 多对多
  ┌──────────┼──────┐        │                │
  ▼          ▼      ▼        │                │
Ability   Project  Exp       │                │
Card      Card     Card      │                │
                             │                │
                ┌────────────┼────────────┐   │
                ▼            ▼            ▼   │
            JobPosting  ResumeBranch[] Investment[] (v1 轻)
                                              ▲
                                              │
                            (v2 扩 interview_sessions / offers)
```

### 核心实体

#### User
```yaml
id, 微信openid / email, nickname
persona_type: 应届 / 社招 / 转行   # 影响 AI prompt 分支
preferences: { 伪装模式开关, 默认简历模板, 默认语言 zh/en }
created_at, last_active_at
```

#### MasterResume（每 User 1 份）
```yaml
id, user_id, basic_info{姓名,电话,邮箱,地点,在职状态}
ability_cards: AbilityCard[]
project_cards: ProjectCard[]
experience_cards: ExperienceCard[]
parsed_from_file_url
quality_score
updated_at
```

#### AbilityCard / ProjectCard / ExperienceCard

**AbilityCard**
```yaml
id, master_resume_id, skill_name, evidence_text, level(1-5)
last_used_year, tags[], is_weak
```

**ProjectCard**（最重要，未来面试模块的题库基础）
```yaml
id, master_resume_id, project_name, role, period
scale_data{用户量/GMV/团队规模/...}
star: { situation, task, action, result }
tech_stack[], domain_tags[]
is_weak, weak_reasons[]
cross_domain_translation: {}   # v1 仅转行人填，其他人留空
```

**ExperienceCard**
```yaml
id, master_resume_id, company, period, title, scope
achievements: string[], industry
is_current   # true 时 UI 触发隐私强提示，导出默认脱敏为"某知名互联网公司"
```

#### Application（数据模型核心）
```yaml
id, user_id
status   # v1: drafting/archived  ·  v2 扩: applied/interviewing/offered/rejected
job_posting: JobPosting
resume_branches: ResumeBranch[]
investments: Investment[]              # v1 做实
linked_resources: ResourceItem[]       # 多对多
priority(1-5), notes
created_at, last_active_at
# v2/v3 留空字段
interview_sessions: []
offers: []
```

#### JobPosting（Application 内嵌）
```yaml
raw_text, source_url, company_name, job_title, department
salary_range, location, language(zh/en)
requirements_parsed{硬技能[], 软技能[], 经验[]}
hidden_preferences[], red_flags[]
parsed_at
```

#### ResumeBranch（补丁分支）
```yaml
id, application_id, version_label("v1","v2",...)
based_on_master_at         # 基于哪个时间点的主版本（用于 diff）
patch: PatchOperations[]   # 关键：存操作而非全文本
ai_reasoning               # 修改理由
match_score
language(zh/en)            # 这版的输出语言
exported_pdf_url[], created_at, is_active
```

**PatchOperations 设计**（核心机制）：
```yaml
operations:
  - { type: reorder, card_id: P1, new_position: 1 }
  - { type: emphasize, card_id: A3, intensity: high }
  - { type: rewrite, card_id: P2, field: "result", new_text: "..." }
  - { type: hide, card_id: P5 }
  - { type: insert_keyword, card_id: A1, keywords: ["增长","数据"] }
```

好处：主版本一改，所有分支自动重算；diff 渲染极快；存储极省。

#### Investment（v1 做实，轻量）
```yaml
id, application_id, used_resume_branch_id
action_type   # 已投 / 已读 / 已约面 / 已收 offer / 已拒
action_at, channel, notes
```

#### ResourceItem
```yaml
id, user_id, type   # 面经 / 公司情报 / 招聘者背景 / 行业资料 / 其他
title, content_text, source_url, attachments[]
linked_applications[], linked_company_names[]
tags[], created_at
ai_summary, ai_extracted_signals[]
```

#### ResourceCollection（资源合集）
```yaml
id, user_id, name, description, resource_items[], created_at
```

#### WeeklyDigest（本周复盘 · 缓存）
```yaml
id, user_id, week_of("2026-06-22")
stats: { new_apps, new_branches, exports, coach_inquiries }
ai_observation_text
suggested_actions[]
generated_at
```

#### CoachInquiry（增值导流记录）
```yaml
id, user_id, application_id, source_screen
contact_method, status(new/contacted/converted), notes
```

### 隐私与存储

| 数据 | 存储位置 | 加密 |
|---|---|---|
| 主简历原文件 | 对象存储（私有 bucket，24h 预签名 URL） | 服务端加密 |
| 结构化卡片 | 数据库 | 字段级加密：手机/邮箱/在职公司名 |
| JD 文本、AI 输出 | 数据库 | 不加密（无 PII） |
| 伪装模式开关 | 本地 + 服务端同步 | — |
| `is_current=true` 经历 | 数据库 | UI 强提示 + 导出默认脱敏 |

---

## §5 AI 用法、成本边界 + 免费/付费切分

### AI 调用清单

> **统一供应商**：用户侧所有 LLM 调用都走 **MiniMax**（重活 MiniMax-M1，轻活 abab6.5s-chat）。下表成本为 MiniMax 公开价折算（参考价：M1 输入 ¥6/M、输出 ¥24/M；abab6.5s 输入/输出 ¥1/M；¥7 ≈ $1）。

| # | 场景 | 模型 | 单次成本（¥） | 单次成本（$） | 频次 |
|---|---|---|---|---|---|
| 1 | 简历解析 → 卡片 | MiniMax-M1 | ~¥0.10 | ~$0.014 | 每用户 1-3 次 |
| 2 | 主简历含金量诊断 | MiniMax-M1 | ~¥0.04 | ~$0.006 | 每用户 1-3 次 |
| 3 | 应届生轻问诊 | abab6.5s | ~¥0.012 | ~$0.002 | 应届生 1 次 |
| 4 | JD 解析 | abab6.5s | ~¥0.004 | ~$0.0006 | 每 JD 1 次 |
| 5 | 补丁分支生成 + 理由 | MiniMax-M1 | ~¥0.12 | ~$0.017 | 每 JD 1-3 次 |
| 6 | 简历评分 | abab6.5s | ~¥0.002 | ~$0.0003 | 每分支 1 次 |
| 7 | 资源摘要 + 信号提取 | abab6.5s | ~¥0.003 | ~$0.0004 | 每资源 1 次 |
| 8 | 本周观察 | MiniMax-M1 | ~¥0.06 | ~$0.009 | 每周 1 次 |
| 9 | 跨域映射（转行） | MiniMax-M1 | ~¥0.08 | ~$0.011 | 每项目卡 1 次 |

### 单用户月成本（缓存优化后）

- 轻度用户（5 JD/月）：**~¥1.2** (~$0.17)
- 典型用户（10 JD/月）：**~¥2-3** (~$0.3-0.4)
- 重度用户（30 JD/月）：**~¥6** (~$0.85)

### 关键优化（必做）

1. **MiniMax Context Caching**：主简历卡片在多次补丁生成中复用 → 命中后缓存部分价格约为原价 1/3，整体成本降 ~70%
2. **小模型先筛**：JD 解析、资源摘要、评分用 abab6.5s（M1 约 6× 价格）
3. **结果存档**：所有 AI 输出落库，重复查看不重复调用

### 免费容量上限

| 资源 | 上限 | 超量 |
|---|---|---|
| 主简历 | 1 份 | — |
| 进行中机会 | 20 | 提示归档 |
| 月新建机会 | 15 | 导流 Coach |
| 月补丁分支 | 30 | 导流 Coach |
| 资源条目 | 100 | 导流 Coach |
| 资源合集 | 5 | 导流 Coach |
| 周复盘 | 无限 | — |

### 商业回本逻辑

- 200 MAU · 月 AI 成本 ~¥600（约 $85 USD）
- Coach 单价 ¥500-2000 · 转化率 1% = 2 单 → 覆盖成本

### 技术决策

- LiteLLM 抽象层 + MiniMax-M1 → abab6.5s 同家族两档兜底（统一调用 MiniMax）
- 每次调用打点（user_id, scene, tokens, cost）→ 内部成本仪表盘（4 张图：用户量 / 调用量 / 单 user 成本 / 总开销）
- 单用户 RPM 限流

### v1 不做（避免成本黑洞）

- 实时对话式简历修改
- 多模型 ensemble
- 流式生成 + 中途修改

---

## §6 风险、边界 + 北极星指标

### 七大风险与缓解

| # | 风险 | 缓解 |
|---|---|---|
| 1 | AI 解析质量差 | 必有"手动校对/补全"流程 + AI 标"低置信"字段 |
| 2 | 补丁过度优化 | 改写幅度上限 ≤ 30% + 每条理由 + 一键回滚 |
| 3 | 隐私事故 | 字段级加密 + 预签名 URL + is_current 强提示 + 默认脱敏 + 审计日志 |
| 4 | MiniMax 单点依赖 | LiteLLM 抽象层 + M1→abab6.5s 同家族两档兜底；保留双 API key 槽位 + 国内（api.minimax.chat）/ 海外（api.minimaxi.chat）双 endpoint 备用；如未来需多供应商，仅扩 LiteLLM provider 配置即可 |
| 5 | JD 抓取合规 | v1 默认不爬，仅粘贴；链接抓取留 v1.5 + robots 提示 |
| 6 | 成本失控 | 日上限 + 总成本上限 + 红线自动降级 + 短信告警 |
| 7 | Coach 瓶颈 | v1 每周固定 5 slot，售完显示"下周再约"+ 录入候选 coach 资源 |

### v1 明确不做

| 类别 | 不做 |
|---|---|
| 简历视觉 | 模板市场、字体定制（中英各 1 个内置模板） |
| 平台 | 小程序、App、桌面端、浏览器插件 |
| 账号 | 团队账号、多账号切换、子账号 |
| 社交 | 内推、社区、UGC、分享、收藏 |
| 数据获取 | 主动爬取招聘平台、第三方 API、邮件自动抓取 |
| AI 功能 | 实时对话改稿、模拟面试、多 agent 评审、面经自动生成 |
| 商业化 | 订阅会员、credits、企业版、ToB |
| 移动 | 仅响应式（手机可看不可编辑） |

### v1 英文/双语范围

| 子项 | v1 必做 |
|---|---|
| 网站 UI 中英切换 | ✅ |
| 英文简历解析 | ✅ |
| 英文简历导出（1 个简洁模板） | ✅ |
| 英文 JD 基础解析 | ✅ |
| 英文补丁生成 + diff | ✅ |
| 本周复盘英文版 | ✅ |
| 资源库英文资源 AI 摘要 | ✅ |
| 转行人英文跨域映射 | 🟡 v1.5 |
| 英文措辞地道度评分 | 🟡 v1.5 |

### 北极星指标

**WACS = Weekly Active Customized Resumes**
> 周活用户在一周内完成"生成补丁分支 + 导出 PDF"算 1 次

### 辅助指标（3 月目标）

| 维度 | 指标 | 目标 |
|---|---|---|
| 激活 | 注册 24h 内完成首次定制率 | ≥ 50% |
| 质量 | 首次端到端定制时长（上传 → 导出，含 AI 处理） | ≤ 3 分钟 |
| 粘性 | W2 留存率 | ≥ 25% |
| 深度 | 周活人均 WACS | ≥ 1.5 |
| 资源使用 | 周活人均资源新增数 | ≥ 3 |
| 复盘 | 周复盘打开率 | ≥ 40% |
| 变现 | Coach 导流转化率（点击→付费） | ≥ 5% |
| 成本 | 单活跃用户 AI 成本 | ≤ $0.8 |

### 3 月成功判定

```
✅ 全绿（v2 全力投入）：
  100+ 注册 · 40+ WAU · 周人均 WACS 1.5+ · Coach 5+ 单/月 · W2 留存 25%+

🟡 半数达成（迭代 1 月再决策）：
  60+ WAU 但留存或 WACS 不达预期 → 集中 1 月优化留存与 Aha

🔴 未达成（pivot 或放弃）：
  W2 留存 < 15% 或周人均 WACS < 0.5 → 价值主张需要重新审视
```

### 产品哲学（六条）

1. **省时优于完美**：宁可 3 分钟出 80 分，不要 15 分钟出 95 分
2. **透明优于聪明**：AI 每个修改必须给"为什么"，不做黑盒
3. **可逆优于自动**：所有 AI 修改可回滚，所有数据可导出
4. **协助优于替代**：用户始终是简历的"作者"，AI 是"主编"
5. **隐私优于增长**：永远不主动分享、不索取通讯录、不做"求职者社交"
6. **陪伴优于工具**：v1 是简历工具，但骨架与数据为"长期陪伴"而设计，每多用一次成本越低、效果越好

---

## 附录：v1 范围一句话清单

**v1 做**：
中英双语 Web 工作台 / 三人群（应届/社招/转行）/ 主简历库（卡片化）/ 求职机会列表（5 列 tab 仅亮简历）/ 简历定制（主版本+补丁分支+diff+理由）/ 投递记录（轻）/ 资源库（含合集）/ 本周复盘（含 AI 观察）/ Coach 导流 / 伪装界面 / 中英简历模板（各 1）/ 现公司默认脱敏 / 成本仪表盘

**v1 不做**：
小程序/App/插件 / 内推社区 / 模板市场 / 实时对话改稿 / 模拟面试 / 多 agent 评审 / 主动爬取 / 订阅会员 / 团队账号 / ToB

---

## 下一步

1. 用户审阅本文档
2. 调用 `writing-plans` skill 生成实施计划（按 v1 范围拆 sprint）
