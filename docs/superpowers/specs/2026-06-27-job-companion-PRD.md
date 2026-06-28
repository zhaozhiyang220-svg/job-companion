# PRD — Job Companion v1（求职作战中心）

> **Status**: Ready for Agent
> **Source Spec**: `docs/superpowers/specs/2026-06-27-job-companion-design.md`
> **Implementation Plans**: `docs/superpowers/plans/2026-06-27-plan-0..7-*.md`
> **Generated via**: mattpocock/skills@to-prd
> **Label (manual)**: `ready-for-agent`

---

## Problem Statement

**我是在职跳槽 1-5 年的产品/运营/技术/设计/数据从业者**。

我每天 23:00 在床上刷 Boss 看到一个心动岗位，恨不得立刻投出去，但每次都遇到同一个死结：**我的简历是为现在这份工作写的，不是为这个岗位写的**。

如果用 ChatGPT 改，会改得太狠失真，而且每次都要从头喂上下文；如果用超级简历这类 SaaS，是模板套娃，看不出来"为什么改这里"；如果直接交真人 coach，单次 500-2000 元、还要等几天。

更糟的是：

- 我有 N 个目标岗位，每个都得定制一遍——但**没人帮我系统沉淀"主简历"**，每次都是改一份散一份
- 我**怕被现公司发现**——简历里写"某公司在职"很奇怪，写真名又风险大
- 我**怕被同事突然路过工位**——浏览器一打开就是「我的求职机会」很尴尬
- 我**不知道自己投了多少**、**改了几版**、**哪个岗位还没动**——一个月下来回头看完全是浆糊
- 我应届/转行的朋友更惨：**他们连"主简历"都拼不出来**

我需要的不是另一个简历工具，是**一个长期陪我跑求职这件事的工作台**——但它必须从第一天就好用，否则我没耐心。

## Solution

**Job Companion**：一个 Web 工作台，针对在职跳槽 / 应届校招 / 跨行业转行 三类求职者。

核心心智：**主简历是 master，每个 JD 是一个 patch 分支**——你的能力库/项目库/经历库沉淀一次，每个岗位 AI 自动生成"补丁分支"调整关键词/优先级/措辞，diff 透明可见、可回滚、可对比。

核心体验：

1. **3 分钟拿到第一份定制简历**：上传简历 → AI 解析为结构化卡片 → 粘 JD → AI 生成补丁分支 + 标注修改理由 → 一键导出 PDF（中/英）
2. **第二次起 ≤ 90 秒**：主简历已沉淀，新 JD 直接生成新分支
3. **隐私优先**：现公司导出默认脱敏为「某知名互联网公司」；全局快捷键 Ctrl+\` 一键切换"番茄钟+待办"伪装界面
4. **作战中心心智**：所有求职机会以 Application 为中心组织，5 列 Tab（简历定制 / 投递记录 / 面试准备 v2 / 面试复盘 v3 / Offer 评估 v3）从第一天就让用户看到完整路线图
5. **本周复盘**：周中任何时候打开都能看到"本周共定制 N 版、AI 观察到你最近在 X 方向集中"+ 建议下一步
6. **资源库**：面经/公司情报/招聘者背景/行业资料 横向沉淀，AI 摘要 + 信号提取，可关联到具体机会喂给简历定制
7. **免费 + Coach 导流**：AI 部分免费、靠口碑跑量；用户在简历页/容量超限处可一键提交真人 Coach 锐评申请（500-2000/次，每周 5 slot），PM 自接

## User Stories

### A. 注册 / 登录 / 用户身份

1. As a 在职跳槽者, I want 用微信扫码登录, so that 不暴露个人邮箱
2. As a 海外求职者, I want 用邮箱 Magic Link 登录, so that 不依赖微信
3. As a 首次用户, I want 登录后选择求职阶段（应届/社招/转行）, so that AI 的解析与补丁逻辑能针对我优化
4. As a 用户, I want 修改昵称和阶段偏好, so that 我能在用着用着发现"其实我现在是转行"时调整
5. As a 隐私敏感用户, I want 我的邮箱在数据库里是字段级加密的, so that 即使数据库被脱库我的身份也不立即泄露

### B. 上传 / 解析 / 构建主简历

6. As a 社招跳槽者, I want 拖拽 PDF/Word 简历上传, so that 我不用手填一遍
7. As a 用户, I want 上传后 30 秒内看到 AI 把简历拆成「能力卡 + 项目卡 + 经历卡」, so that 我感受到"我的简历被透视"的 Aha
8. As a 用户, I want 每张卡片可单独编辑（inline edit）, so that 我能修正 AI 解析错的地方
9. As a 用户, I want AI 自动标记"含金量低"的卡片（无数据/无背景/词不达意）, so that 我知道哪些地方该补强
10. As a 用户, I want 主动触发"AI 含金量诊断", so that 我能在重大修改后重新评估
11. As a 应届校招生, I want AI 5-8 轮对话挖出我的实习/项目/竞赛/课程经历, so that 我的简历不是空的
12. As a 应届生, I want 在 AI 觉得收集够了时按"完成"一键转为主简历, so that 我无需自己组装
13. As a 跨行业转行者, I want 我的经历卡片被打上"原行业"标签, so that 后续补丁能做跨域翻译
14. As a 在职用户, I want 我的"现公司"经历卡有醒目的隐私提示, so that 我不会忘记它会暴露我

### C. 求职机会 / JD 解析

15. As a 用户, I want 点"+ 新增机会"粘贴 JD 文本, so that AI 自动抓出公司/岗位/部门/薪资/硬技能/软技能/隐性偏好/雷区
16. As a 用户, I want 看到求职机会列表（含全部 / 进行中 / 已归档 三个 tab）, so that 我能管理同时进行的多个机会
17. As a 用户, I want 把不再投的机会归档, so that 列表不被噪音淹没
18. As a 用户, I want 在机会卡片上看到当前简历版本号 + 评分 + 最近更新时间, so that 不进详情也能看进度
19. As a 用户, I want 同时进行的机会不超过 20 个, so that 系统强迫我聚焦
20. As a 用户, I want 30 天内新建机会数超过 15 时弹出"是否找 Coach 帮聚焦", so that 系统在我贪心时拉我一把
21. As a 用户, I want 进入单个机会后看到 5 列 Tab（简历 / 投递 / 面试准备 / 面试复盘 / Offer 评估）, so that 我从第一天就理解这是个长期陪我跑的工作台
22. As a v1 用户, I want 灰显的 v2/v3 Tab 鼠标悬浮提示"即将上线 · 这里会做什么", so that 我感受到产品的路线图而非画饼

### D. 简历定制 / 补丁分支（核心）

23. As a 用户, I want 在某机会下点"生成第一版定制简历", so that AI 在主简历基础上生成针对该 JD 的补丁分支
24. As a 用户, I want 看到补丁分支的对比视图（默认并排：左 master / 右补丁）, so that 我直观看到改了什么
25. As a 用户, I want 切换三种模式：diff 高亮 / 并排对比 / 合并预览（导出前所见即所得）, so that 不同审阅习惯都被支持
26. As a 用户, I want 每条 AI 修改都附带"为什么改"理由说明, so that 我感受到被赋能而非被替代
27. As a 用户, I want 单字段改写幅度被硬约束在 30% 以内, so that AI 不会改到我自己都不认识
28. As a 用户, I want 生成失败（如改写超 30%）时收到明确错误, so that 我能选择"重新生成"或"手动调整"
29. As a 用户, I want 同一机会可有多个版本（v1/v2/v3）, so that 我能 A/B 试不同方向
30. As a 用户, I want 在版本之间快速切换, so that 我比较哪一版更好
31. As a 用户, I want 回滚到某个历史版本, so that 不慎改坏可以撤销
32. As a 用户, I want 看到本分支对该 JD 的匹配评分（0-100）, so that 我有量化反馈
33. As a 用户, I want 主版本被修改后所有分支自动重算（PatchOps 应用在 master 副本上）, so that 我维护一份就好
34. As a 转行用户, I want 补丁分支启用"跨域映射"模式, so that 我前一份行业的"GMV"被翻译成新行业的等价指标

### E. 导出 PDF / 隐私

35. As a 用户, I want 一键导出当前分支为中文 PDF, so that 我能立刻投出去
36. As a 海外求职用户, I want 导出英文 PDF, so that 投递外企
37. As a 在职用户, I want "现公司脱敏"导出选项默认 ON, so that 现公司名自动替换为「某知名互联网公司 / Major Tech Company」
38. As a 用户, I want 在导出对话框看到清楚说明（脱敏为什么 / 不脱敏会怎样）, so that 我做有意识的选择
39. As a 用户, I want 每次导出的 PDF 链接保存 7 天, so that 我能反复下载/分享
40. As a 用户, I want 导出 PDF 中字体支持中英文混排（思源 + Inter）, so that 排版美观

### F. JD 解读侧栏

41. As a 用户, I want 在简历定制页左侧看到 JD 解读：关键词 / 隐性偏好 / 雷区 / 匹配评分, so that 改简历时一目了然
42. As a 用户, I want 看到 JD 的"雷区"提示（如全员持股潜台词、扁平管理实则无层级感）, so that 我警觉
43. As a 用户, I want 在侧栏看到与该机会"已关联资源"列表, so that 我能调用面经/公司情报作为简历定制上下文

### G. 投递记录（Investments）

44. As a 用户, I want 在机会的"投递记录"Tab 新增动作（已投/已读/已约面/已收 offer/已拒）, so that 我记录求职轨迹
45. As a 用户, I want 每条投递动作可关联"使用的简历版本", so that 未来面试时能追溯"我给这家投的是哪版"
46. As a 用户, I want 选投递渠道（Boss/拉勾/猎聘/LinkedIn/官网/内推/其他）, so that 我能复盘哪个渠道更有效
47. As a 用户, I want 投递记录按时间线倒序展示, so that 一眼看到最新状态
48. As a 用户, I want 编辑或删除已记录的动作, so that 改正录错的信息

### H. 资源库（Resources）

49. As a 用户, I want 新建资源条目（面经/公司情报/招聘者背景/行业资料/其他）, so that 我把求职原料沉淀下来
50. As a 用户, I want AI 自动给资源生成 1-3 句摘要, so that 我之后扫一眼就能想起来
51. As a 用户, I want AI 提取资源中的关键信号（question_pattern / culture_signal / process_step / salary_anchor）, so that 我能直接用来准备简历或面试
52. As a 用户, I want AI 识别资源中提到的公司名, so that 关联到机会更容易
53. As a 用户, I want 按类型筛选资源（全部 / 面经 / 公司情报 / 招聘者背景 / 行业资料 / 其他）, so that 找东西快
54. As a 用户, I want 新建"资源合集"（如"字节面试"、"消费品方向"）, so that 把相关资源分组
55. As a 用户, I want 把资源加入/移出合集, so that 灵活组织
56. As a 用户, I want 在合集 sidebar 上看到每个合集的资源数, so that 心中有数
57. As a 用户, I want 一个资源可同时挂在多个合集和多个机会下, so that 同一份面经可同时为"字节合集"和"豆包 PM 机会"服务
58. As a 用户, I want 资源数超过 100 / 合集数超过 5 时弹"找 Coach 帮聚焦", so that 系统在我囤积太多时引导我

### I. 本周复盘（Weekly Recap）

59. As a 用户, I want 一级入口"本周复盘"任何时候打开都能看, so that 周中也能复盘
60. As a 用户, I want 看到本周统计：新增机会 / 定制版本 / 导出 PDF / Coach 询问 / 进行中机会总数, so that 量化感知节奏
61. As a 用户, I want 看到 AI 本周观察（"你这周 75% 集中在增长方向"）, so that 我看到自己看不见的模式
62. As a 用户, I want AI 给 1-3 条建议下一步（如"去补强主简历的数据驱动卡"）, so that 我有具体行动方向
63. As a 用户, I want 建议下一步是可点击的（跳转到对应模块）, so that 一键执行
64. As a 用户, I want 切换历史周（最近 12 周）, so that 我能复盘"上个月怎么样"
65. As a 用户, I want 点"重算本周"立刻生成最新, so that 不必等周一 cron
66. As a 用户, I want 周一 00:30 BJT 系统自动预生成上周 digest, so that 周日已结束我周一就能直接看

### J. Coach 导流 / 真人锐评

67. As a 用户, I want 在简历定制页 / 容量超限处一键打开"找 Coach 锐评"抽屉, so that 想付费时不必跑别处
68. As a 用户, I want 看到本周 Coach slot 剩余数, so that 知道是否售罄
69. As a 用户, I want 提交 Coach 申请时填联系方式（微信/手机/邮箱）+ 想被锐评的环节备注, so that PM 能精准服务
70. As a 用户, I want 本周 slot 售罄时表单替换为"留邮箱下周通知我"入口, so that 不空手而归
71. As a 用户, I want 一级入口 `/coach` 完整介绍 Coach 服务（价位 500-2000、流程 30-60 分钟、本周剩余）, so that 我做决策有依据
72. As a PM, I want 用户提交 Coach 申请时我立刻收到 webhook 通知（飞书/Telegram/邮件三选一）, so that 我 24h 内能联系用户

### K. 伪装界面

73. As a 在职用户, I want 全局快捷键 Ctrl+\` 切到伪装界面, so that 老板突然路过时秒切
74. As a 在职用户, I want 伪装界面是番茄钟 + 待办清单, so that 一眼看上去合理
75. As a 在职用户, I want 浏览器 tab 标题切换为「TimeFlow - Pomodoro & Tasks」+ favicon 变番茄, so that 即使切到别的 tab 时被瞥见也不暴露
76. As a 在职用户, I want 再按 Ctrl+\` 秒回原状, so that 危险解除后立即回来工作

### L. 国际化 / 双语

77. As a 用户, I want 网站右上角一键切中文/English, so that 我能选择更舒适的界面
78. As a 海外求职用户, I want 上传英文简历能被正确解析, so that 一份主简历跨语言通用
79. As a 海外求职用户, I want 英文 JD 解析能正常工作（基础关键词 + 硬技能）, so that 投外企也能用
80. As a 用户, I want AI 输出（包括 diff、本周观察）跟随当前语言, so that 不混语言
81. As a 在职用户, I want 中英简历模板各 1 个简洁版, so that v1 不必纠结模板

### M. 内部 / PM Dashboard

82. As PM, I want 用密码访问 `/internal/dashboard`, so that 我看运营数据但用户访问不了
83. As PM, I want 看到 4 个 KPI（DAU / MAU / Total Users / Coach 本周）+ 4 个 AI 成本 KPI（今日/30 天 调用量与成本）, so that 我快速判断业务健康度
84. As PM, I want 看到 30 天的 DAU / AI calls / AI cost 折线图, so that 我看趋势
85. As PM, I want 密码缓存在 sessionStorage 一次, so that 查看不必重输

### N. 全局体验

86. As a 用户, I want 所有 AI 输出（除非加载中）都被持久化在数据库, so that 我刷新页面不重跑（也省成本）
87. As a 用户, I want 所有数据可一键导出（GDPR 友好）, so that 我能离开时拿走我的资产
88. As a 用户, I want 所有可逆操作（删除资源、删除分支等）都有二次确认, so that 不误删
89. As a 用户, I want 操作失败时看到清晰错误（不是 "Network Error"）, so that 我知道下一步怎么办
90. As a 用户, I want 在所有页面都能看到一致的左侧导航 + 右上角伪装/语言按钮, so that 心智一致

## Implementation Decisions

### 架构原则

- **数据中心是 Application（求职机会），不是 Resume**：MasterResume 与 ResumeBranch 都围绕 Application 组织；这一决策让 v2 加面试模块时只需"加 tab + 实现该 tab"，无需重构 v1
- **主简历存原子卡片，不存大段文本**：AbilityCard / ProjectCard / ExperienceCard 三类卡片是 v2 面试模块的"项目深挖题库"基础
- **补丁存操作而非全文**：ResumeBranch 的 patch 字段存 PatchOperations 列表（reorder / emphasize / rewrite / hide / insert_keyword），而非简历快照——主版本一改所有分支自动重算，diff 渲染极快，存储省 90%+

### 关键模块（高层接口，不含文件路径）

- **LLM 抽象层**：所有 AI 调用走统一 `LLMClient.acomplete(model, system, messages, user_id, scene)`，自动写 `ai_call_logs` 表（成本仪表盘底盘）。**用户侧统一调用 MiniMax**，fallback 链：`auto-m1` → MiniMax-M1 → abab6.5s-chat（同家族两档兜底）；`auto-light` → abab6.5s-chat
- **Context Caching**：补丁生成调用上对 master 序列化部分启用 **MiniMax Context Caching**，命中后仅按增量 token 计费，预计单次成本降 ~70%（MiniMax 缓存命中价约为原价 1/3）
- **PatchOperations DSL**：
  ```typescript
  type Op =
    | { type:'reorder', card_id:str, new_position:int }
    | { type:'emphasize', card_id:str, intensity:'low'|'medium'|'high' }
    | { type:'rewrite', card_id:str, field:str, new_text:str }
    | { type:'hide', card_id:str }
    | { type:'insert_keyword', card_id:str, keywords:[str] }
  ```
  `apply_operations(master, ops)` 是纯函数，单字段改写超 30% 抛 `RewriteTooLargeError`
- **字段级加密**：手机/邮箱/在职公司名用 Fernet 加密；`email_lookup_hash`（sha256）用于唯一约束与查询
- **JWT Session**：HTTPOnly cookie `jc_session`，30 天 TTL，HS256
- **次级唯一约束**：每用户 1 份 MasterResume；每 Application 1 份 JobPosting；每 user × week_of 1 份 WeeklyDigest

### Schema 关键决策

- `applications.status`：v1 仅 `drafting/archived`，但枚举预留 `applied/interviewing/offered/rejected`（v2 启用），不再迁移
- `application_resource_links`：在 Plan 2 先建表，Plan 4 创建 ResourceItem 后补 FK
- `resume_branches.patch`：JSON 列存 PatchOperations 数组；`ai_reasoning` JSON 列存 [{op_index, reason}]，UI 必展示
- `experience_cards.company_encrypted`：加密；明文走 service 层 decrypt；导出 PDF 时根据 `is_current` + `mask_current_company` flag 渲染为「某知名互联网公司」或真名

### API 契约（高层）

- 所有业务 endpoint 路径前缀 `/api/v1/`，内部仪表盘前缀 `/internal/`
- 容量超限统一返回 HTTP 409 + `{detail: {code, message}}`，code 包括 `capacity_active / capacity_monthly / capacity_resources / capacity_collections / coach_full`
- 错误码驱动前端 `<CapacityGate code, onClose>` 组件 → Coach 导流

### AI 成本控制

- 重操作（解析 / 补丁生成 / 含金量诊断 / 跨域映射 / 本周观察）用 **MiniMax-M1**
- 轻操作（JD 解析 / 资源摘要 / 评分 / 应届轻问诊）用 **abab6.5s-chat**
- 单活跃用户月成本目标 ≤ ¥3（缓存优化后；约 $0.4 USD，较原 Anthropic 方案再降 ~50%）
- 三级开关防失控：单用户日上限 + 总成本日上限 + 红线自动降级到 abab6.5s + 短信告警

### 容量门设计（容量 / 商业混合杠杆）

- 20 进行中机会 / 月 15 新建机会 / 100 资源 / 5 合集 / 周 5 Coach slot
- 触达上限统一弹 `<CapacityGate>` → 直接打开 Coach Inquiry Drawer，把"限制"转化为变现入口

### 周划分

- 周一 00:00 ~ 周日 23:59:59 北京时区（`zoneinfo("Asia/Shanghai")`）
- `WeeklyDigest.week_of` = 该周周一日期（UTC date）
- APScheduler 周一 00:30 BJT 触发预生成上周 digest

### 国际化

- `next-intl` 框架 + 路由前缀 `/zh/` `/en/`，默认 zh
- 翻译文件按模块 namespace（home / nav / auth / master_resume / opportunities / resume_tab / resources / investments / weekly / coach 等）
- AI prompt 中传 `output_language` 参数，AI 输出语言跟随
- 中英简历模板各 1 个（zh_simple.html / en_simple.html），共用 base.css

### 鉴权

- 双通道：邮箱 Magic Link（默认）+ 微信扫码（开放平台）
- 首次登录自动注册；夸渠道登录用同 email_lookup_hash / wechat_openid 唯一查
- 应届/社招/转行 persona 选择放在登录后的 onboarding step

### 监控

- Sentry：前后端未捕获异常自动上报
- PostHog：所有关键用户行为强类型枚举打点（`packages/shared-types/events.ts`），事件清单已在 7 个 plan 中明确
- 内部成本仪表盘：4 张 SVG 图（不引外部 chart 库）+ KPI 卡片

## Testing Decisions

### 什么是好测试

- **只测对外行为，不测实现细节**：测端点输入输出、测组件渲染、测纯函数输入输出；不测 SQL 字符串、不测内部方法名
- **TDD 节奏**：每个 task 按"写失败测试 → 实现 → 跑通 → commit"，每个 step 2-5 分钟
- **AI 调用必须 mock**：不在 CI 跑真实 LLM；用 `unittest.mock.patch + AsyncMock` 模拟 `LLMClient.acomplete` 的返回，固定 JSON 字符串
- **测真实 DB**：API 测试不 mock SQLAlchemy，跑真实 Postgres（CI 用 service container）→ 防迁移漂移

### 测试覆盖矩阵

| 模块 | 单元测试 | 接口测试 (TestClient) | e2e (Playwright) |
|---|---|---|---|
| PatchOps DSL | ✅ apply + 5 op 类型 + 30% guard | — | — |
| LLMClient + AI 调用打点 | ✅ mock LLM + 验证写 log | — | — |
| Auth (Magic Link / WeChat / JWT) | ✅ JWT roundtrip + token 过期 | ✅ 登录全流程 + cookie | ✅ login 页可达 |
| MasterResume CRUD | — | ✅ upload-init / parse / cards | smoke |
| Application + JD parse | — | ✅ create + list + 容量门 | smoke |
| ResumeBranch | — | ✅ generate + diff + 导出 + 回滚 | smoke |
| Resources + Collections | — | ✅ CRUD + 多对多 | smoke |
| Investments | — | ✅ CRUD + 时间线 | — |
| WeeklyDigest | ✅ 时区/统计逻辑 | ✅ get/refresh/history | smoke |
| Coach + Notifier | — | ✅ availability + create + capacity_full | smoke |
| Internal Dashboard | ✅ password middleware | ✅ summary + timeseries | password gate |

### Prior Art

- **TDD 范式**：参考 Plan 0 Task 3-5（health endpoint、Settings、User model 的"先写失败测试 → 实现 → 跑通"流程）
- **Mock AI**：所有 AI service 测试统一用 `patch("path._llm.acomplete", AsyncMock(return_value=json.dumps(...)))`，Plan 1-3 反复出现
- **DB Fixture**：参考 Plan 0 Task 5 的 `conftest.py`（session-scoped engine + per-test rollback）

### CI 流水线

- GitHub Actions 双 job：`web`（lint + typecheck + vitest + playwright e2e）+ `api`（ruff + mypy + alembic upgrade + pytest）
- 每个 PR 必跑；e2e 跑关键路径冒烟（不依赖真实 LLM，依赖 mock）
- Postgres 用 service container；Field encryption key 临时生成

## Out of Scope

### v1 完全不做

- **平台**：小程序 / 移动 App / 浏览器插件 / Mac/Win 桌面端（响应式可看不可编辑）
- **简历视觉**：模板市场 / 字体定制 / 颜色定制（仅中英各 1 个简洁内置模板）
- **账号体系**：团队账号 / 多账号切换 / 子账号 / 企业版
- **社交**：内推 / 社区 / UGC / 评论 / 收藏分享 / 朋友圈
- **数据获取**：主动爬取 Boss/拉勾 / 邮件自动抓取 / 第三方招聘 API
- **AI 功能**：实时对话式简历修改 / 模拟面试 / 多 agent 评审 / 面经自动生成
- **商业化**：订阅会员 / credits 充值 / 企业版 / ToB
- **5 列 Tab v2/v3**：面试准备 / 面试复盘 / Offer 评估（仅灰显路线图）

### v1 不深做（v1.5 缓做）

- 英文措辞地道度评分
- 转行人英文跨域映射深度逻辑
- JD 链接抓取（v1 仅手动粘贴）
- 浏览器插件
- 转行人卡片"原行业 → 新行业"自动翻译（v1 仅打标）

### v1.5 / v2 / v3 演进

- v1.5：英文体验加固 + 浏览器插件 + JD 链接抓取
- v2：面试准备（JD 拆解 + 预测题库 + AI 模拟面试 copilot）+ 多 agent 锐评（付费墙第一站）
- v3：面试复盘（录音转写 + AI 反馈）+ Offer 评估（多 offer 对比 + 谈薪）+ 小程序

## Further Notes

### 北极星指标
**WACS = Weekly Active Customized Resumes**（周活用户在一周内"生成补丁分支 + 导出 PDF"次数）

### 3 月成功判定（v1 上线后）
- ✅ 全绿：100+ 注册 · 40+ WAU · 周人均 WACS 1.5+ · Coach 5+ 单/月 · W2 留存 25%+
- 🟡 半绿：60+ WAU 但留存或 WACS 不达预期 → 集中 1 月优化
- 🔴 未达：W2 留存 < 15% 或周人均 WACS < 0.5 → pivot 或放弃

### 产品哲学（6 条，进每个 plan 文档头部约束）
1. 省时优于完美
2. 透明优于聪明
3. 可逆优于自动
4. 协助优于替代
5. 隐私优于增长
6. 陪伴优于工具

### 商业回本逻辑
200 MAU · 月 AI 成本 ~¥600（约 $85 USD，较原 Anthropic 方案 $150 再降 ~40%）；Coach 单次 ¥500-2000，转化率 1% (2 单/月) 即覆盖成本

### 团队 / 资源约束
- 个人独开（1-2 人）/ 3-4 月窗口
- 技术栈固化：Next.js 15 + FastAPI + Postgres + Redis + LiteLLM + WeasyPrint + 微信扫码 + next-intl + PostHog + Sentry + Playwright
- 部署：Vercel（前端）+ Fly.io 或 阿里云 ECS（后端）+ Supabase（DB）

### 已知风险（七大）
1. AI 解析质量差 → 手动校对兜底 + 低置信字段标注
2. 补丁过度优化 → 30% 改写硬约束 + 每条理由 + 回滚
3. 隐私事故 → 字段加密 + 预签名 URL + is_current 强提示 + 默认脱敏 + 审计日志
4. MiniMax 单点依赖 → LiteLLM + M1→abab6.5s 同家族两档兜底；保留双 API key 槽位 + 国内外双 endpoint 备用
5. JD 抓取合规 → v1 默认仅粘贴，不主动爬
6. 成本失控 → 三级开关 + 单用户日上限 + 总成本日上限 + 短信告警
7. Coach 瓶颈 → 周 5 slot + 售罄 UI + 邮件订阅候补

### 实施计划（已产出）
- `docs/superpowers/plans/2026-06-27-job-companion-v1-overview.md`（8 plan 高阶 outline）
- 7 份详细 plan：Plan 0-7，共 81 task / 350+ bite-sized step / 估时 16-18 周
- 推荐执行方式：subagent-driven（每 task 一个 fresh subagent，主会话 review）

---

> **如何发布到 issue tracker**：
> - **GitHub Issues**：`gh issue create --title "[PRD] Job Companion v1" --body-file docs/superpowers/specs/2026-06-27-job-companion-PRD.md --label ready-for-agent`
> - **Linear**：复制本文件内容到新 issue，加 `ready-for-agent` 标签
> - **飞书 / Notion**：粘贴 markdown 即可（两者都原生支持）
