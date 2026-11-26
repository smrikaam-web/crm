import { describe, it, expect } from 'vitest'
import {
  SUB_STATUS_OPTIONS_MAP,
  getSubStatusOptions,
  isSubStatusRequired,
} from '@/utils/statusOptions'

describe('statusOptions utility', () => {
  it('defines correct sub-status options mapping', () => {
    expect(SUB_STATUS_OPTIONS_MAP['Not Contacted']).toEqual([
      'Voice mail',
      'No answer',
    ])
    expect(SUB_STATUS_OPTIONS_MAP['Not Valid']).toEqual([
      'Wrong number',
      'Others',
    ])
    expect(SUB_STATUS_OPTIONS_MAP['Contacted']).toBeUndefined()
  })

  it('returns dependent options for Not Contacted', () => {
    const options = getSubStatusOptions('Not Contacted')
    expect(options).toEqual(['Voice mail', 'No answer'])
  })

  it('returns dependent options for Not Valid', () => {
    const options = getSubStatusOptions('Not Valid')
    expect(options).toEqual(['Wrong number', 'Others'])
  })

  it('returns empty array for Contacted', () => {
    const options = getSubStatusOptions('Contacted')
    expect(options).toEqual([])
  })

  it('returns empty array for unknown or empty status', () => {
    expect(getSubStatusOptions('')).toEqual([])
    expect(getSubStatusOptions(null)).toEqual([])
    expect(getSubStatusOptions(undefined)).toEqual([])
    expect(getSubStatusOptions('NonExistent')).toEqual([])
  })

  it('identifies when Sub Status is required', () => {
    expect(isSubStatusRequired('Not Contacted')).toBe(true)
    expect(isSubStatusRequired('Not Valid')).toBe(true)
    expect(isSubStatusRequired('Contacted')).toBe(false)
    expect(isSubStatusRequired('')).toBe(false)
    expect(isSubStatusRequired(null)).toBe(false)
  })
})
