import type { Config } from 'tailwindcss'

// Swiss Modernism 2.0 — 语义色映射到 globals.css 的 CSS 变量；
// tailwind 默认的 neutral/black/white/red/green 仍可用（组件大量使用）。
export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        'bg-subtle': 'var(--color-bg-subtle)',
        'bg-muted': 'var(--color-bg-muted)',
        'bg-inverse': 'var(--color-bg-inverse)',
        fg: 'var(--color-fg)',
        'fg-muted': 'var(--color-fg-muted)',
        'fg-subtle': 'var(--color-fg-subtle)',
        'fg-inverse': 'var(--color-fg-inverse)',
        border: 'var(--color-border)',
        'border-strong': 'var(--color-border-strong)',
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          fg: 'var(--color-accent-fg)',
          soft: 'var(--color-accent-soft)',
        },
        success: 'var(--color-success)',
        destructive: 'var(--color-destructive)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'var(--font-sans-cn)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        none: '0px',
        sm: '2px',
        md: '4px',
        lg: '8px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgba(0,0,0,0.04)',
        md: '0 4px 12px -2px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config
