# 求职作战中心 · UI/UX 设计规范（Swiss Modernism 2.0）

> **版本**：v1.0 · 2026-06-27
> **基础风格**：Swiss Modernism 2.0（瑞士现代主义 2.0）
> **基础设施依据**：ui-ux-pro-max skill recommendation · WCAG 2.2 AA+ / 部分 AAA
> **配套文档**：
> - 产品 PRD：`docs/superpowers/specs/2026-06-27-job-companion-PRD.md`
> - 技术方案：`TECH_DESIGN.md`
> - Landing 原型：`landing-prototypes/option-a-swiss/`（参考实现）

---

## 0. 文档使用说明

本文档是后续正式做网页（Landing + 主产品）的**唯一视觉设计依据**。所有页面、所有组件、所有交互都必须从这份文档查找规则。

- **设计师**：以本文档为 Figma 库的源头。改动必须同步回本文档。
- **前端**：所有 CSS 变量、Tailwind utility、组件样式严格遵循 §2-§4 的 token 与组件规格。
- **PM**：在写需求/审稿时按 §11 的 voice & tone 写文案。

---

## 1. 设计哲学与原则

### 1.1 为什么选 Swiss Modernism 2.0

| 选择依据 | 解释 |
|---|---|
| **目标用户**：26-32 岁白领、产品/运营/技术/数据岗，每天用 Linear/Notion/Figma | 这些用户已被严肃工具的视觉语言教育，对花哨设计反感 |
| **产品定位**：严肃的求职工作台，不是娱乐产品 | 求职关乎收入与人生，需要"信得过"的视觉气质 |
| **核心心智**："主版本 + 补丁分支" 像 Git | Swiss 的网格秩序与代码思维同构 |
| **隐私护城河**：默认脱敏 + 伪装界面 | 克制的视觉天然不引人注目，符合在职党"低调"的心理 |
| **国际化**：中英双语 + 海外求职场景 | Swiss 是全球设计共识，文化通用 |

### 1.2 五条不可违背的设计原则

1. **网格优先于装饰**——所有页面用严格 12 列网格。不能解释为什么的元素一律删掉。
2. **黑白主导，单一 accent**——主色只用纯黑/纯白。Accent (#FF4500) 仅用于关键 CTA、链接下划线、状态点。**禁止**为了"好看"加第二个 accent。
3. **字体表达层级，颜色不表达层级**——通过字号、字重、字距建立信息层级。颜色只承担"语义"职能（accent / muted / destructive）。
4. **留白是设计的一部分**——大面积留白是 Swiss 的灵魂。宁可少放内容，不可挤满屏幕。
5. **可访问性 ≥ 美观**——任何视觉决策若与 WCAG 冲突，可访问性优先。Swiss 风格本身就是 WCAG AAA 友好。

### 1.3 三条禁忌（任何 PR 触发自动拒绝）

- ❌ **使用 emoji 作为结构性图标**（导航、按钮、状态）——一律用 lucide-react SVG
- ❌ **在同一页面使用两种以上 accent 色**——只允许 #FF4500
- ❌ **任意改动 12 列网格**——所有布局必须 `grid-cols-12` 起步

---

## 2. 设计 Tokens（设计令牌）

### 2.1 颜色系统

#### Primitive Tokens（原始色）— 只在 token 层使用

```css
/* === Primitive Tokens === */
/* 中性色（11 级灰阶） */
--gray-0:    #FFFFFF;
--gray-50:   #FAFAFA;
--gray-100:  #F5F5F5;
--gray-200:  #E5E5E5;
--gray-300:  #D4D4D4;
--gray-400:  #A3A3A3;
--gray-500:  #737373;
--gray-600:  #525252;
--gray-700:  #404040;
--gray-800:  #262626;
--gray-900:  #171717;
--gray-1000: #000000;

/* Accent（单一红橙） */
--orange-50:  #FFF1EB;
--orange-500: #FF4500;   /* 主 accent · WCAG 4.5:1 against white */
--orange-600: #E63E00;

/* 语义色（仅这两个，禁止扩展） */
--red-600:    #DC2626;   /* destructive 唯一 */
--green-600:  #16A34A;   /* success 唯一 */
```

#### Semantic Tokens（语义色）— 组件层使用

```css
/* === Semantic Tokens · Light Mode === */
--color-bg:              var(--gray-0);       /* 主背景 */
--color-bg-elevated:     var(--gray-0);       /* 卡片背景（Swiss 不分层） */
--color-bg-subtle:       var(--gray-50);      /* 次级背景 / hover */
--color-bg-muted:        var(--gray-100);     /* metric bar / sidebar */
--color-bg-inverse:      var(--gray-1000);    /* 反转区（隐私段、底部 CTA）*/

--color-fg:              var(--gray-1000);    /* 主文本 */
--color-fg-muted:        var(--gray-600);     /* 次级文本 */
--color-fg-subtle:       var(--gray-400);     /* 提示/占位 */
--color-fg-inverse:      var(--gray-0);       /* 反转区文本 */

--color-border:          var(--gray-200);     /* 弱边框（卡片、分割线） */
--color-border-strong:   var(--gray-1000);    /* 强边框（按钮、章节分割）*/
--color-border-muted:    var(--gray-100);     /* 极弱边框 */

--color-accent:          var(--orange-500);
--color-accent-fg:       var(--gray-0);
--color-accent-hover:    var(--orange-600);

--color-destructive:     var(--red-600);
--color-success:         var(--green-600);

--color-ring:            var(--gray-1000);    /* focus ring 一律黑色 */
```

#### Dark Mode 映射

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg:              var(--gray-1000);
    --color-bg-elevated:     var(--gray-900);
    --color-bg-subtle:       var(--gray-900);
    --color-bg-muted:        var(--gray-800);
    --color-bg-inverse:      var(--gray-0);

    --color-fg:              var(--gray-0);
    --color-fg-muted:        var(--gray-400);
    --color-fg-subtle:       var(--gray-500);
    --color-fg-inverse:      var(--gray-1000);

    --color-border:          var(--gray-800);
    --color-border-strong:   var(--gray-0);
    --color-border-muted:    var(--gray-900);

    --color-ring:            var(--gray-0);
  }
}
```

#### 对比度核查（必过）

| 组合 | 比率 | WCAG |
|---|---|---|
| `fg` on `bg`（黑/白） | 21:1 | AAA |
| `fg-muted` on `bg`（gray-600/白） | 7.5:1 | AAA |
| `fg-subtle` on `bg`（gray-400/白） | 3.4:1 | AA Large only |
| `accent` (#FF4500) on `bg` | 4.6:1 | AA normal text |
| `accent-fg` on `accent` | 4.6:1 | AA normal text |
| `fg-inverse` on `bg-inverse` | 21:1 | AAA |

⚠️ `fg-subtle` 仅可用于 ≥18px 的标签、placeholder、装饰性 caption；不能用于正文。

### 2.2 字体系统

#### 字体选择

```css
--font-sans: 'Inter', 'Noto Sans SC', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Noto Sans Mono CJK SC', ui-monospace, monospace;

/* Google Fonts 导入（生产用 next/font 自托管，不走 CDN） */
/* @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap'); */
```

**字体选择理由**：
- **Inter**：英文 SaaS 共识字体，可读性 + 数字 tabular（Stripe/Linear/Vercel/Figma 都在用）
- **Noto Sans SC**：中文字符兜底，与 Inter 笔画粗细匹配最好的中文字体之一
- **JetBrains Mono**：代码感 + 等宽数字（用于版本号 `v3`、`patch v2`、KPI 数字）

#### Type Scale（10 级）

| Token | 字号 | 行高 | 字重 | 字距 | 使用场景 |
|---|---|---|---|---|---|
| `display-2xl` | `clamp(3rem, 8vw, 7rem)` | 0.95 | 900 | -0.04em | Hero 首屏标题 |
| `display-xl` | `clamp(2.5rem, 6vw, 5rem)` | 0.95 | 800 | -0.04em | 页面级 H1 |
| `display-lg` | `clamp(2rem, 5vw, 4rem)` | 1.0 | 800 | -0.03em | 章节 H2 |
| `display-md` | `clamp(1.5rem, 3vw, 2.5rem)` | 1.1 | 700 | -0.02em | 卡片标题、Section H3 |
| `heading` | 1.5rem (24px) | 1.2 | 700 | -0.015em | 小标题 |
| `subheading` | 1.125rem (18px) | 1.3 | 600 | -0.01em | 列表项标题、卡片副标题 |
| `body-lg` | 1.125rem (18px) | 1.6 | 400 | 0 | Hero 副文案、长 quote |
| `body` | 1rem (16px) | 1.6 | 400 | 0 | **默认正文**（最低字号） |
| `body-sm` | 0.875rem (14px) | 1.5 | 400 | 0 | 次级文本、按钮、表单 |
| `label` | 0.75rem (12px) | 1.4 | 500 | 0.02em | 章节编号、标签、metric label |

⚠️ **不许低于 12px**。中文低于 14px 阅读体验下降，正文一律 ≥ 16px。

#### Font Feature 设置

```css
body {
  font-feature-settings:
    'cv02', 'cv03', 'cv04',  /* Inter 字形变体 - 更几何的 1/4/6 */
    'ss01',                  /* Inter Stylistic Set 1 */
    'tnum';                  /* 等宽数字（避免数字列对不齐）*/
  letter-spacing: -0.01em;   /* 默认略微紧凑（Swiss 偏好）*/
}

/* 中文段落微调（Noto Sans SC 默认偏宽松）*/
:lang(zh), .text-cn {
  letter-spacing: 0.01em;
  font-feature-settings: normal;
}

/* 代码/数据强制等宽数字 */
.tabular { font-variant-numeric: tabular-nums; }
.mono    { font-family: var(--font-mono); }
```

#### 章节编号系统（Swiss 特色）

每个章节顶部用 `§NN` 标记。Mono 字体、`label` token、accent 色：

```css
.section-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;          /* 12px */
  font-weight: 500;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--color-fg);
}
.section-label::before { content: '§'; margin-right: 0.25em; color: var(--color-accent); }
```

例：`§01 — Workflow`、`§02 — Comparison`、`§03 — Privacy`。

### 2.3 间距系统（8pt 基准 + 12 列网格）

#### 间距 Tokens

```css
--space-0:  0;
--space-1:  4px;    /* 0.5x */
--space-2:  8px;    /* 1x · 基础单位 */
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
--space-32: 128px;
```

**使用规则**：
- 组件内部 padding：`space-3` ~ `space-6`
- 组件之间 gap：`space-4` ~ `space-8`
- 卡片之间 gap：`space-6`
- 章节之间 padding-y：`space-24` ~ `space-32`
- 永远不使用非 token 的数值（禁止 `padding: 13px`）

#### 12 列网格

```css
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;   /* 16px gutter */
}

/* 容器最大宽度 */
.container { max-width: 1440px; margin-inline: auto; padding-inline: 32px; }
@media (max-width: 768px) { .container { padding-inline: 16px; } }
```

**常见跨列模式**：
- 全宽：`col-span-12`
- 8/4 分（文 + 卡）：`md:col-span-8 + md:col-span-4`
- 4/8 分（meta + 主）：`md:col-span-4 + md:col-span-8`
- 三等分：3×`md:col-span-4`
- 四等分（metric bar）：4×`md:col-span-3`

⚠️ **不许出现** `col-span-5`、`col-span-7` 这类奇数跨度（破坏数学美感）。

### 2.4 圆角 / 边框 / 阴影

#### 圆角（Swiss 偏好直角，谨慎使用圆角）

```css
--radius-none:  0px;       /* 默认 · 卡片、按钮、输入 */
--radius-sm:    2px;       /* 极轻微 · tag */
--radius-md:    4px;       /* 表单字段、code 块 */
--radius-lg:    8px;       /* 极少用 · 仅 toast、tooltip */
--radius-full:  9999px;    /* 禁用 · Swiss 不用 pill 形 */
```

⚠️ **不用** `rounded-2xl` 这类大圆角。Swiss 风格 95% 场景是直角。

#### 边框

```css
--border-1:     1px solid var(--color-border);        /* 卡片、分割线 */
--border-2:     2px solid var(--color-border-strong); /* 强分割 */
--border-strong: 1px solid var(--color-border-strong);/* 按钮、章节分隔 */
```

**使用规则**：
- 卡片：`border: 1px solid var(--color-border)`（gray-200）
- 章节分隔：`border-top: 1px solid var(--color-fg)`（纯黑）
- 表格：行间 `border-b: 1px solid var(--color-border)`
- 按钮：`border: 1px solid currentColor`

#### 阴影（极度克制）

```css
--shadow-none:  none;        /* 默认 · 99% 场景 */
--shadow-sm:    0 1px 2px 0 rgba(0,0,0,0.04);   /* 仅 toast / dropdown */
--shadow-md:    0 4px 12px -2px rgba(0,0,0,0.08); /* 仅 modal */
```

⚠️ **Swiss 设计原则上无阴影**。需要"卡片感"时用边框，不用阴影。仅浮层（modal/toast/dropdown）允许极轻阴影。

### 2.5 动效系统

#### Duration

```css
--duration-instant: 0ms;     /* 显隐切换 · 减少 GPU */
--duration-fast:    150ms;   /* 按压、hover */
--duration-base:    200ms;   /* 颜色变化、边框变化 */
--duration-slow:    300ms;   /* 模态入场、Sheet 滑动 */
--duration-slower:  500ms;   /* 极少用 · 复杂转场 */
```

#### Easing

```css
--ease-out:     cubic-bezier(0.16, 1, 0.3, 1);     /* 入场（默认）*/
--ease-in:      cubic-bezier(0.7, 0, 0.84, 0);     /* 退场 */
--ease-in-out:  cubic-bezier(0.65, 0, 0.35, 1);    /* 状态切换 */
--ease-linear:  linear;                             /* 进度条 / loading */
```

#### 通用模式

```css
/* 按压反馈 */
.btn-press { transition: transform 150ms var(--ease-out); }
.btn-press:active { transform: scale(0.97); }

/* hover 颜色变化 */
.color-hover { transition: background-color 200ms var(--ease-out), color 200ms var(--ease-out); }

/* 折叠展开 */
.disclosure-icon { transition: transform 200ms var(--ease-in-out); }
.disclosure[open] .disclosure-icon { transform: rotate(45deg); }
```

#### Reduced Motion（强制）

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 2.6 响应式断点

```css
--bp-sm:  640px;   /* 大手机横屏 */
--bp-md:  768px;   /* 平板竖屏 · 主要分界 */
--bp-lg:  1024px;  /* 平板横屏 / 小桌面 */
--bp-xl:  1280px;  /* 桌面 */
--bp-2xl: 1440px;  /* 大桌面 · 内容最大宽 */
```

**Tailwind 4 调用**：
```html
<!-- 例：col-span-12 md:col-span-8 -->
<div class="col-span-12 md:col-span-8">...</div>
```

**测试断点（必测）**：375 / 768 / 1024 / 1440 px

---

## 3. 图标系统

### 3.1 图标库

**默认**：[lucide-react](https://lucide.dev/)（与 Plan 0-7 一致）

```bash
npm install lucide-react
```

### 3.2 图标规则

| 规则 | 标准 |
|---|---|
| **来源唯一** | 整个产品只用 lucide-react 一套，不混用 |
| **笔画粗细** | 默认 `strokeWidth={2}`，强调时 `{2.5}` 或 `{3}` |
| **尺寸 token** | `icon-xs: 12px` / `icon-sm: 16px` / `icon-md: 20px` / `icon-lg: 24px` |
| **触达区** | 图标若可点击，外层需 ≥ 44×44px tap area（用 `padding` 撑大）|
| **颜色** | 跟随 `currentColor`，不要硬编码 |
| **a11y** | 仅图标按钮必有 `aria-label`；装饰性图标加 `aria-hidden="true"` |

### 3.3 常用图标映射

| 场景 | 图标 |
|---|---|
| 求职机会 | `Briefcase` |
| 主简历 | `FileText` |
| 资源库 | `BookOpen` |
| 周复盘 | `BarChart3` |
| Coach | `MessageSquareQuote` |
| 简历定制 | `Sparkles` |
| 投递记录 | `Send` |
| 设置 | `Settings` |
| 用户 | `UserCircle2` |
| 隐私/锁 | `ShieldCheck` / `Lock` |
| 伪装界面 | `Eye` / `EyeOff` |
| 补丁分支 | `GitBranch` |
| 加号/添加 | `Plus` |
| 关闭/移除 | `X` |
| 展开/折叠 | `ChevronDown` / `ChevronRight` |
| 主要 CTA 箭头 | `ArrowRight` / `ArrowUpRight` |
| 时间/速度 | `Clock` / `Zap` |
| 检查/通过 | `Check` |
| 警告 | `AlertTriangle` |
| 错误 | `XCircle` |
| 成功 | `CheckCircle2` |

---

## 4. 组件库规格

### 4.1 Button

#### 变体

| 变体 | 用途 | 样式 |
|---|---|---|
| **Primary** | 主 CTA（每页 ≤ 1 个） | 黑底白字 / hover gray-800 |
| **Secondary** | 次要操作 | 白底黑字 + 黑边 / hover gray-50 |
| **Ghost** | 弱操作（导航链接、取消） | 无边无底 / hover gray-100 |
| **Destructive** | 删除 / 危险 | red-600 底白字 / hover red-700 |
| **Accent** | 关键转化 CTA（首页大按钮、final CTA） | accent 底白字 / hover orange-600 |

#### 尺寸

| Size | Height | Padding-X | Font |
|---|---|---|---|
| `sm` | 32px (h-8) | 12px (px-3) | body-sm (14px) |
| `md` (默认) | 40px (h-10) | 16px (px-4) | body (16px) |
| `lg` | 48px (h-12) | 24px (px-6) | body (16px) |
| `xl` | 56px (h-14) | 32px (px-8) | subheading (18px) |

#### Tailwind 4 实现

```tsx
// components/Button.tsx
import { type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'ghost' | 'destructive' | 'accent'
type Size = 'sm' | 'md' | 'lg' | 'xl'

const variants: Record<Variant, string> = {
  primary:     'bg-black text-white border border-black hover:bg-neutral-800',
  secondary:   'bg-white text-black border border-black hover:bg-neutral-50',
  ghost:       'bg-transparent text-black hover:bg-neutral-100',
  destructive: 'bg-red-600 text-white border border-red-600 hover:bg-red-700',
  accent:      'bg-[--color-accent] text-white border border-[--color-accent] hover:bg-[--color-accent-hover]',
}

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-base',
  lg: 'h-12 px-6 text-base',
  xl: 'h-14 px-8 text-lg',
}

export function Button({
  variant = 'primary', size = 'md', className, ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium tracking-tight',
        'transition-colors duration-200 active:scale-[0.97] transition-transform',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2',
        'disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  )
}
```

#### 使用规则
- 一页 1 个 primary（最重要的 CTA）
- icon + text 时，icon 在文字左边，`<Icon className="w-4 h-4" />`
- loading 状态：禁用 + 显示 spinner
- 移动端 size 至少 `md`（保证 44px 触达）

### 4.2 Input / Form Field

```tsx
// components/Input.tsx
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'h-12 w-full px-4 text-base bg-white border border-black',
        'placeholder:text-neutral-400',
        'focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-0',
        'disabled:bg-neutral-100 disabled:cursor-not-allowed',
        'aria-invalid:border-red-600 aria-invalid:ring-red-600',
        className,
      )}
      {...props}
    />
  )
}

// components/FormField.tsx
export function FormField({ label, error, hint, required, children }: {
  label: string; error?: string; hint?: string; required?: boolean; children: ReactNode
}) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-black">
        {label}{required && <span className="text-red-600 ml-0.5">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-neutral-600">{hint}</p>}
      {error && <p className="text-xs text-red-600" role="alert">{error}</p>}
    </div>
  )
}
```

**规则**：
- Label 永远在 input 上方（不许 placeholder 替代 label）
- Error 在字段下方 + 红色 + `role="alert"`
- 必填字段右上角红色星号
- focus ring 2px 黑色（不是默认蓝色）

### 4.3 Card

```tsx
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'bg-white border border-neutral-200 p-6',
        'transition-colors duration-200 hover:border-black',
        className,
      )}
      {...props}
    />
  )
}
```

**规则**：
- 默认无圆角（Swiss 风）
- 无阴影，只用边框
- hover 时边框变黑（弱反馈）
- 内部 padding 24px

### 4.4 Table

```tsx
<table className="w-full text-sm">
  <thead>
    <tr className="border-b-2 border-black">
      <th className="text-left py-4 font-mono text-xs uppercase tracking-widest text-neutral-600">
        Capability
      </th>
      {/* ... */}
    </tr>
  </thead>
  <tbody>
    <tr className="border-b border-neutral-200">
      <td className="py-4 pr-8 font-medium">Master resume reuse</td>
      <td className="py-4 pr-8">✓ Card-based</td>
    </tr>
  </tbody>
</table>
```

**规则**：
- header 用 mono 字体 + uppercase + tracking-widest
- header 底部 2px 黑边，行间 1px 灰边
- 行高 ≥ 56px（py-4 + 文本行高）
- 移动端：超过 4 列时改为卡片堆叠或水平滚动 + 视觉提示

### 4.5 Modal / Dialog

```tsx
// 推荐：使用 Radix UI Dialog + 自定义样式
<Dialog>
  <DialogOverlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
  <DialogContent className="
    fixed left-[50%] top-[50%] -translate-x-1/2 -translate-y-1/2
    w-full max-w-lg bg-white border border-black p-8
    shadow-md  /* 仅 modal 允许阴影 */
  ">
    {/* ... */}
  </DialogContent>
</Dialog>
```

**规则**：
- 遮罩 `bg-black/60` + 4px backdrop-blur
- 弹层无圆角 + 1px 黑边
- 关闭按钮（X 图标）在右上角，触达 44×44
- Esc 关闭 + 点击遮罩关闭（破坏性操作需二次确认时禁用）
- focus trap 自动 + 关闭后 focus 返回触发元素

### 4.6 Toast / Notification

```tsx
<div
  role="status"
  aria-live="polite"
  className="
    fixed top-6 right-6 z-50
    bg-white border border-black p-4 max-w-sm
    shadow-sm
    animate-in slide-in-from-top-2 duration-200
  "
>
  <div className="flex gap-3">
    <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
    <div>
      <p className="font-medium text-sm">操作成功</p>
      <p className="text-sm text-neutral-600 mt-1">补丁分支 v3 已生成。</p>
    </div>
  </div>
</div>
```

**规则**：
- `role="status" + aria-live="polite"`（不打断屏幕阅读）
- 自动消失 3-5s
- 成功/错误用 lucide-react 图标 + 语义色
- 单次最多 3 个 toast 堆叠

### 4.7 Badge / Tag

```tsx
// 普通 tag
<span className="inline-flex items-center px-2 py-0.5 text-xs font-mono bg-neutral-100 text-neutral-700 border border-neutral-200">
  增长
</span>

// Match score（accent）
<span className="inline-flex items-center px-2 py-0.5 text-xs font-mono bg-[--color-accent]/10 text-[--color-accent] border border-[--color-accent]/20">
  match 82
</span>

// Patch 标记（产品特有）
<span className="patch-tag">v3 · patch</span>
```

```css
.patch-tag {
  display: inline-flex; align-items: center;
  padding: 2px 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--color-bg-muted);
  color: var(--color-fg);
  border: 1px solid var(--color-border);
}
```

### 4.8 Navigation / Header

```tsx
<header className="sticky top-0 z-50 bg-white border-b border-black">
  <div className="container h-16 flex items-center justify-between">
    <Link href="/" className="font-bold tracking-tight text-lg flex items-center gap-2">
      <span className="w-7 h-7 bg-black text-white flex items-center justify-center font-mono text-sm">JC</span>
      <span>job/companion</span>
    </Link>
    <nav className="hidden md:flex items-center gap-10 text-sm font-medium">
      <a href="#workflow">Workflow</a>
      <a href="#privacy">Privacy</a>
    </nav>
    <Button size="sm" variant="primary">Start free</Button>
  </div>
</header>
```

**规则**：
- 高度 64px（h-16），固定 + sticky
- 底部 1px 黑边（不是 shadow）
- Logo 左、导航中、CTA 右
- 移动端：导航折叠到汉堡菜单（Sheet 模式）

### 4.9 Tabs

```tsx
<div role="tablist" className="border-b border-neutral-200 flex gap-8">
  {tabs.map((tab, i) => (
    <button
      key={tab.key}
      role="tab"
      aria-selected={activeIndex === i}
      className={cn(
        'pb-3 text-sm font-medium border-b-2 -mb-px transition-colors',
        activeIndex === i
          ? 'border-black text-black'
          : 'border-transparent text-neutral-500 hover:text-black'
      )}
    >
      {tab.label}
    </button>
  ))}
</div>
```

**规则**：
- 选中态：底部 2px 黑边 + 文字黑色
- 未选中：text-neutral-500 + 无边
- 灰显（v2/v3 未上线）：`text-neutral-300 cursor-not-allowed` + 悬浮提示

### 4.10 Empty State

```tsx
<div className="text-center py-20 border border-dashed border-neutral-300">
  <FileText className="w-12 h-12 mx-auto text-neutral-300 mb-4" />
  <h3 className="text-lg font-semibold mb-2">还没有求职机会</h3>
  <p className="text-sm text-neutral-600 mb-6">粘贴一份 JD 开始第一份定制。</p>
  <Button variant="primary" size="md">
    <Plus className="w-4 h-4" /> 新增机会
  </Button>
</div>
```

**规则**：
- 居中布局 + 虚线边框框定空白区
- 大图标（48px）+ 标题 + 描述 + CTA
- 描述说明"为什么空"和"如何不空"

---

## 5. 页面模板

### 5.1 Landing Page（已实现，参考 `landing-prototypes/option-a-swiss/`）

```
Section §00 — Nav (h-16, sticky)
Section §01 — Hero (大字 + metrics bar)
Section §02 — Workflow (3 步)
Section §03 — vs ChatGPT (表格)
Section §04 — Privacy (黑底反转)
Section §05 — Personas (3 列)
Section §06 — Coach
Section §07 — FAQ (折叠)
Section §08 — Final CTA (黑底)
Section §09 — Footer
```

### 5.2 Dashboard 主页（App Layout）

```
┌─────────────────────────────────────────────────┐
│  Header (h-16, bottom border)                   │
├─────┬───────────────────────────────────────────┤
│     │                                           │
│ Sde │  Main Content (max-w-content, p-8)        │
│ Nav │  ┌──────────────────────────────────────┐ │
│ w64 │  │  §01 · 本周概览 (4 metric cards)     │ │
│     │  ├──────────────────────────────────────┤ │
│     │  │  §02 · 进行中机会 (3 列卡片)         │ │
│     │  ├──────────────────────────────────────┤ │
│     │  │  §03 · AI 本周观察                    │ │
│     │  └──────────────────────────────────────┘ │
└─────┴───────────────────────────────────────────┘
```

**关键规则**：
- 侧边导航宽 256px (w-64)，右侧 1px 黑边
- 主区域 padding 32px，max-width 1200px
- 章节间距 80px (space-20)

### 5.3 单机会 5 列 Tab 页

```
┌─────────────────────────────────────────────────┐
│  Breadcrumb: 求职机会 / 字节跳动 - PM           │
├─────────────────────────────────────────────────┤
│  H1: 字节跳动 · 高级产品经理 · 豆包业务         │
│  Meta: 30-50k · 北京 · 3天前更新                │
├─────────────────────────────────────────────────┤
│  Tabs: [简历定制 ✓] [投递记录 ✓] [面试 🔒v2]    │
├─────────────────────────────────────────────────┤
│  Active Tab Content                             │
└─────────────────────────────────────────────────┘
```

### 5.4 简历定制双视图

```
┌──────────────────────┬─────────────────────────┐
│  JD 解读侧栏 (w-72)  │  对比视图               │
│  · 关键词            │  ┌──────────┬──────────┐│
│  · 隐性偏好          │  │ master   │ patch v3 ││
│  · 雷区              │  │ (mono底)  │ (高亮)  ││
│  · match score       │  │          │          ││
│  ────────────        │  │  cards   │  cards   ││
│  已关联资源          │  └──────────┴──────────┘│
│                      │  AI 修改理由 (折叠)     │
└──────────────────────┴─────────────────────────┘
```

**规则**：
- 左栏固定宽 288px (w-72)，右栏 flex-1
- 双视图：1px 黑色中线分割
- 高亮：patch 改动用 accent 色下划线（不用底色）
- 修改理由列表用 mono 字体显示 op_index

### 5.5 资源库

```
┌─────────────────────────────────────────────────┐
│  Type Filter Tabs                               │
├──────┬──────────────────────────────────────────┤
│ Coll │  Resource Cards (3 列 grid 或 list)      │
│ ecti │  ┌────────────────────────────────────┐  │
│ on   │  │ Icon + Title + AI Summary          │  │
│ List │  │ Companies · Signals · Tags         │  │
│ w-56 │  └────────────────────────────────────┘  │
└──────┴──────────────────────────────────────────┘
```

### 5.6 内部成本仪表盘（密码保护）

```
┌─────────────────────────────────────────────────┐
│  4 Big KPI Cards (display-md 数字 + label)      │
│  DAU · MAU · Total · Coach 本周                 │
├─────────────────────────────────────────────────┤
│  4 AI Cost KPI Cards                            │
├─────────────────────────────────────────────────┤
│  Chart 1: DAU 30 天折线 (纯 SVG)                │
│  Chart 2: AI Calls 30 天折线                    │
│  Chart 3: AI Cost 30 天折线                     │
└─────────────────────────────────────────────────┘
```

---

## 6. 可访问性（WCAG 2.2）

### 6.1 必过项（v1 上线前自动审计）

- [ ] 所有正文 ≥ 16px
- [ ] 所有颜色组合 ≥ 4.5:1（大字 ≥ 3:1）
- [ ] 所有可交互元素触达 ≥ 44×44px
- [ ] 所有图标按钮有 `aria-label`
- [ ] 所有图片有 `alt`（装饰性图片 `alt=""`）
- [ ] focus ring 在所有可 focus 元素上可见（黑色 2px）
- [ ] Tab 键顺序与视觉顺序一致
- [ ] H1-H6 顺序不跳级
- [ ] 表单 label 与 input 用 `for/id` 关联
- [ ] 错误信息靠近字段 + `role="alert"` 或 `aria-live`
- [ ] 不靠颜色单独传达信息（红色 + 文字 / 图标）
- [ ] `prefers-reduced-motion` 已实现
- [ ] 系统字体放大到 200% 不破版

### 6.2 推荐工具

- **axe DevTools** Chrome 插件（CI 集成）
- **Lighthouse** a11y 评分 ≥ 95
- **WAVE** 检查 contrast & ARIA
- **VoiceOver / NVDA** 真机测试关键流程

---

## 7. i18n（中英双语）

### 7.1 字体处理

```css
/* 中英混排：font-family fallback 自动切换 */
font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif;

/* 中文段落微调（letter-spacing 不要太紧）*/
:lang(zh) p, :lang(zh) li, .text-cn p, .text-cn li {
  letter-spacing: 0.01em;
  line-height: 1.7;  /* 中文行距比英文宽 */
}

/* 英文段落保持紧凑 */
:lang(en) p { letter-spacing: -0.01em; line-height: 1.6; }
```

### 7.2 文案差异

| 维度 | 中文 | 英文 |
|---|---|---|
| 行宽 | 35-50 字符 | 60-75 字符 |
| 标题字重 | 700-900 | 800-900 |
| 引号 | 「」中文方括号 | "" smart quote |
| 数字 + 单位 | 间空格 `3 分钟` | 紧贴 `3min` |
| 段落首行缩进 | 不缩进（Web 习惯） | 不缩进 |

### 7.3 翻译键命名

```json
{
  "landing": {
    "hero": {
      "title": "...",
      "subtitle": "...",
      "cta_primary": "...",
      "cta_secondary": "..."
    }
  },
  "common": {
    "loading": "加载中…",
    "error_generic": "出错了，请重试",
    "confirm_delete": "确定删除？"
  }
}
```

**规则**：
- 三层 namespace：`<page>.<section>.<key>`
- common 放跨页通用文案
- 禁止 hardcoded 中文/英文出现在 JSX

---

## 8. 微动效 Pattern

### 8.1 标准入场动效

```tsx
// 内容卡片入场：from-below + fade
<div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
  {content}
</div>

// 模态入场：from-center + scale
<DialogContent className="animate-in fade-in zoom-in-95 duration-200">
  ...
</DialogContent>

// 列表入场：stagger 30ms（最多 8 项）
{items.map((item, i) => (
  <div
    key={item.id}
    className="animate-in fade-in slide-in-from-bottom-1"
    style={{ animationDelay: `${i * 30}ms`, animationDuration: '300ms' }}
  >
    {item.content}
  </div>
))}
```

### 8.2 退场动效

```tsx
// 退场比入场快（60-70%）
<div className="data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=closed]:duration-150">
```

### 8.3 禁用清单

- ❌ Parallax 滚动（可能引起眩晕）
- ❌ 自动播放视频/动画（除非用户主动触发）
- ❌ 长于 500ms 的过渡（影响响应感知）
- ❌ 装饰性动画（动效必须传达"为什么"）

---

## 9. 写作语言（Voice & Tone）

### 9.1 品牌声音三条原则

1. **直接，不绕弯**——"3 分钟拿到第一份定制简历"，不是"轻松高效完成简历优化"
2. **具体，不抽象**——"现公司默认脱敏" 而不是 "保护你的隐私"
3. **平视，不教化**——"我们" 与用户并肩，禁用 "您需要"、"建议您"、"立即升级"

### 9.2 文案标准

| 场景 | ✅ 这样写 | ❌ 不这样写 |
|---|---|---|
| Hero | "主简历是 master，每个 JD 是一个 patch 分支" | "智能简历定制平台，让求职更轻松" |
| Button | "免费开始 · 上传简历" | "立即体验" |
| Error | "邮箱格式不正确，请重新输入" | "操作失败" |
| Empty | "还没有求职机会，先粘贴一份 JD 试试" | "暂无数据" |
| Coach | "本周仅 5 个名额，先到先得" | "有限名额，火速抢购" |

### 9.3 禁用词清单

```
立即 / 一键 / 颠覆 / 革命 / 极致 / 完美 / 卓越
强烈推荐 / 万能 / 终极 / 黑科技 / 全网最强
赋能 / 抓手 / 闭环 / 链路 / 底层逻辑（除非真的在说技术）
您 / 您的（一律用"你"）
```

### 9.4 数字与单位

- 时间："3 分钟"（带空格）、"30 秒"、"24h"
- 价格："¥500-2000"（破折号不空格）、"¥0"（免费用 ¥0 不用 "免费"）
- 比例："≥4.5:1"、"≤30%"、"75%"
- 数量："10+ 个 JD"、"5 个名额"

---

## 10. 设计 → 开发交付清单

每次完成新页面 / 新组件，按这份清单 self-review。CI 也会跑自动审计。

### 10.1 视觉

- [ ] 用 12 列网格，没出现 col-span-5/7
- [ ] 单 accent 色，没出现第二个强调色
- [ ] 字号都从 type scale 取，没出现非 token 数值
- [ ] 间距都是 8 的倍数
- [ ] 边框/分割线统一 1px 灰 或 1-2px 黑
- [ ] 仅 modal/toast/dropdown 有阴影，其他无
- [ ] 圆角 ≤ 8px（默认 0px）

### 10.2 交互

- [ ] 所有按钮 hover + active + focus + disabled 四态都设计
- [ ] 关键操作有 loading 状态（spinner / 禁用）
- [ ] 破坏性操作有二次确认
- [ ] 表单 inline validation（onBlur 触发，不是 onChange）
- [ ] 错误信息靠近字段 + 红色 + role="alert"

### 10.3 可访问性

- [ ] 跑过 axe DevTools，0 critical issue
- [ ] Lighthouse a11y ≥ 95
- [ ] 键盘 Tab 顺序与视觉一致
- [ ] focus ring 在所有可 focus 元素上可见
- [ ] 图标按钮有 aria-label
- [ ] 表单 label 与 input 用 for/id 关联

### 10.4 响应式

- [ ] 375 / 768 / 1024 / 1440 四个断点都测了
- [ ] 没有横向滚动
- [ ] 触达 ≥ 44×44px
- [ ] 长文本可换行不溢出
- [ ] 表格在 < 768px 有降级方案

### 10.5 性能

- [ ] LCP < 2.5s（Lighthouse）
- [ ] CLS < 0.1
- [ ] 图片用 next/image + WebP/AVIF
- [ ] 字体用 next/font 自托管（不走 Google CDN）
- [ ] 长列表 ≥ 50 项用虚拟滚动

### 10.6 文案

- [ ] 没有硬编码中/英文
- [ ] 没有禁用词清单里的词
- [ ] 数字 + 单位格式统一
- [ ] 错误信息说明"原因 + 怎么修"
- [ ] 空状态有 CTA 引导

### 10.7 i18n

- [ ] 中英两版都看过
- [ ] 中文段落 letter-spacing 0.01em
- [ ] 英文段落 letter-spacing -0.01em
- [ ] 中文行距 1.7，英文 1.6
- [ ] 翻译键都在 messages/zh.json + en.json 里

---

## 11. 配套资源

### 11.1 Figma 库（待建）

建议在 Figma 建一个共享库，按以下结构：

```
Job Companion · Design System (Swiss)
├─ 🎨 Foundations
│  ├─ Colors (primitive + semantic, light + dark)
│  ├─ Typography (10 levels)
│  ├─ Spacing (8pt grid)
│  └─ Iconography (lucide-react)
├─ 🧩 Components
│  ├─ Button (5 variants × 4 sizes × 4 states)
│  ├─ Input / FormField
│  ├─ Card
│  ├─ Table
│  ├─ Modal / Dialog
│  ├─ Toast
│  ├─ Badge / Tag
│  ├─ Navigation / Header
│  ├─ Tabs
│  └─ Empty State
└─ 📄 Templates
   ├─ Landing
   ├─ Dashboard
   ├─ Opportunity Detail (5-tab)
   ├─ Resume Customization (双视图)
   ├─ Resource Library
   ├─ Weekly Recap
   └─ Internal Dashboard
```

### 11.2 代码层 Token 同步

把所有 §2 的 token 落到一个文件，跨项目共享：

```
packages/design-tokens/
├── tokens.css           ← :root + @theme inline
├── tokens.ts            ← TypeScript 导出（给 JS 用）
└── tokens.json          ← Style Dictionary 源（生成 Figma 变量）
```

### 11.3 storybook 计划（v1.5）

v1 阶段不必上 Storybook（一人团队收益不大）。v1.5 团队扩到 3 人以上时再上。

---

## 12. 风格演进守则

**Swiss Modernism 不是一成不变。**v1.5+ 可能要松绑的边界：

| 维度 | v1 严格度 | 何时可放宽 |
|---|---|---|
| 单一 accent 色 | 100% 严格 | 若有强分支（如付费版/Coach 服务），允许 Coach 单独一个色 |
| 圆角 ≤ 8px | 100% 严格 | 移动端为主的组件（Sheet、移动卡片）可上 12-16px |
| 无阴影 | 95% 严格 | 高层级浮层（command palette、超大模态）可加 |
| 12 列网格 | 100% 严格 | 永不放宽——这是身份基石 |
| 字号 ≥ 16px | 100% 严格 | 永不放宽——这是 a11y 基石 |

任何例外必须先发 PR 改本文档，再改代码。

---

## 附录 · 关键链接

- 参考实现 Landing：`landing-prototypes/option-a-swiss/page.tsx`
- 全套设计 Tokens CSS：`landing-prototypes/option-a-swiss/globals.css`
- lucide-react 图标库：https://lucide.dev/
- WCAG 2.2 标准：https://www.w3.org/TR/WCAG22/
- Tailwind 4 文档：https://tailwindcss.com/docs

---

**文档结束**。后续 v1.5/v2 演进时与代码、Figma 库同步更新。
