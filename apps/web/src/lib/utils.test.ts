import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn', () => {
  it('joins truthy class names with space', () => {
    expect(cn('a', 'b', null, undefined, false, 'c')).toBe('a b c')
  })

  it('merges conflicting tailwind classes (last wins)', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })
})
