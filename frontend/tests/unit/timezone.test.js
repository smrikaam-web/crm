import { describe, it, expect } from 'vitest'
import {
  isValidIanaTimezone,
  getTimezoneForCountry,
  parseOffsetOrAbbrToIana,
  resolveProspectTimezone,
  getUtcOffset,
  formatProspectLocalTime,
  formatProspectTimezoneDisplay,
  COUNTRY_TIMEZONE_MAP,
} from '@/utils/timezone'

describe('Timezone utilities (frontend/src/utils/timezone.js)', () => {
  describe('isValidIanaTimezone', () => {
    it('returns true for valid IANA timezone identifiers', () => {
      expect(isValidIanaTimezone('Asia/Manila')).toBe(true)
      expect(isValidIanaTimezone('Asia/Muscat')).toBe(true)
      expect(isValidIanaTimezone('Asia/Qatar')).toBe(true)
      expect(isValidIanaTimezone('Europe/Brussels')).toBe(true)
      expect(isValidIanaTimezone('Europe/Amsterdam')).toBe(true)
      expect(isValidIanaTimezone('America/New_York')).toBe(true)
      expect(isValidIanaTimezone('America/Chicago')).toBe(true)
      expect(isValidIanaTimezone('America/Los_Angeles')).toBe(true)
    })

    it('returns false for null, undefined, empty or invalid strings', () => {
      expect(isValidIanaTimezone(null)).toBe(false)
      expect(isValidIanaTimezone(undefined)).toBe(false)
      expect(isValidIanaTimezone('')).toBe(false)
      expect(isValidIanaTimezone('Not Available')).toBe(false)
      expect(isValidIanaTimezone('—')).toBe(false)
      expect(isValidIanaTimezone('Invalid/Zone_Name')).toBe(false)
    })

    it('returns false for raw offset strings like GMT+8 or UTC+03:00', () => {
      expect(isValidIanaTimezone('GMT+8')).toBe(false)
      expect(isValidIanaTimezone('UTC+03:00')).toBe(false)
      expect(isValidIanaTimezone('GMT+3 (AST)')).toBe(false)
    })
  })

  describe('getTimezoneForCountry', () => {
    it('resolves primary IANA timezone for requested key countries', () => {
      expect(getTimezoneForCountry('Philippines')).toBe('Asia/Manila')
      expect(getTimezoneForCountry('ph')).toBe('Asia/Manila')

      expect(getTimezoneForCountry('Oman')).toBe('Asia/Muscat')
      expect(getTimezoneForCountry('om')).toBe('Asia/Muscat')

      expect(getTimezoneForCountry('Qatar')).toBe('Asia/Qatar')
      expect(getTimezoneForCountry('qa')).toBe('Asia/Qatar')

      expect(getTimezoneForCountry('Belgium')).toBe('Europe/Brussels')
      expect(getTimezoneForCountry('be')).toBe('Europe/Brussels')

      expect(getTimezoneForCountry('Netherlands')).toBe('Europe/Amsterdam')
      expect(getTimezoneForCountry('nl')).toBe('Europe/Amsterdam')

      expect(getTimezoneForCountry('United States')).toBe('America/New_York')
      expect(getTimezoneForCountry('USA')).toBe('America/New_York')
      expect(getTimezoneForCountry('us')).toBe('America/New_York')

      expect(getTimezoneForCountry('India')).toBe('Asia/Kolkata')
      expect(getTimezoneForCountry('United Kingdom')).toBe('Europe/London')
    })

    it('returns null for unrecognized or unavailable countries', () => {
      expect(getTimezoneForCountry(null)).toBeNull()
      expect(getTimezoneForCountry('')).toBeNull()
      expect(getTimezoneForCountry('Not Available')).toBeNull()
      expect(getTimezoneForCountry('—')).toBeNull()
      expect(getTimezoneForCountry('Atlantis')).toBeNull()
    })
  })

  describe('resolveProspectTimezone', () => {
    it('prioritizes valid rawTimezone over country', () => {
      const tz = resolveProspectTimezone({
        rawTimezone: 'Asia/Manila',
        country: 'Qatar',
      })
      expect(tz).toBe('Asia/Manila')
    })

    it('prioritizes valid customTimezone over country', () => {
      const tz = resolveProspectTimezone({
        customTimezone: 'America/Chicago',
        country: 'United States',
      })
      expect(tz).toBe('America/Chicago')
    })

    it('resolves Philippines prospect to Asia/Manila', () => {
      expect(resolveProspectTimezone({ country: 'Philippines' })).toBe('Asia/Manila')
      expect(resolveProspectTimezone({ country: 'ph' })).toBe('Asia/Manila')
      expect(resolveProspectTimezone({ country: 'Philippines', timezone: 'GMT+8 (PHT)' })).toBe('Asia/Manila')
    })

    it('resolves Oman prospect to Asia/Muscat', () => {
      expect(resolveProspectTimezone({ country: 'Oman' })).toBe('Asia/Muscat')
      expect(resolveProspectTimezone({ country: 'om' })).toBe('Asia/Muscat')
      expect(resolveProspectTimezone({ country: 'Oman', timezone: 'GMT+4 (GST)' })).toBe('Asia/Muscat')
    })

    it('resolves Qatar prospect to Asia/Qatar', () => {
      expect(resolveProspectTimezone({ country: 'Qatar' })).toBe('Asia/Qatar')
      expect(resolveProspectTimezone({ country: 'qa' })).toBe('Asia/Qatar')
      expect(resolveProspectTimezone({ country: 'Qatar', timezone: 'GMT+3 (AST)' })).toBe('Asia/Qatar')
    })

    it('resolves Belgium prospect to Europe/Brussels', () => {
      expect(resolveProspectTimezone({ country: 'Belgium' })).toBe('Europe/Brussels')
      expect(resolveProspectTimezone({ country: 'be' })).toBe('Europe/Brussels')
    })

    it('resolves Netherlands prospect to Europe/Amsterdam', () => {
      expect(resolveProspectTimezone({ country: 'Netherlands' })).toBe('Europe/Amsterdam')
      expect(resolveProspectTimezone({ country: 'nl' })).toBe('Europe/Amsterdam')
    })

    it('handles United States regional timezones appropriately', () => {
      // Chicago / Central
      expect(
        resolveProspectTimezone({ country: 'United States', timezone: 'America/Chicago' }),
      ).toBe('America/Chicago')
      expect(
        resolveProspectTimezone({ country: 'USA', timezone: 'CST' }),
      ).toBe('America/Chicago')

      // Los Angeles / Pacific
      expect(
        resolveProspectTimezone({ country: 'US', timezone: 'PST' }),
      ).toBe('America/Los_Angeles')

      // Denver / Mountain
      expect(
        resolveProspectTimezone({ country: 'United States', timezone: 'MST' }),
      ).toBe('America/Denver')

      // Default US fallback to Eastern
      expect(
        resolveProspectTimezone({ country: 'United States' }),
      ).toBe('America/New_York')
    })

    it('extracts IANA timezone from formatted abbreviation if country is missing', () => {
      expect(resolveProspectTimezone({ timezone: 'GMT+8 (PHT)' })).toBe('Asia/Manila')
      expect(resolveProspectTimezone({ timezone: 'GMT+4 (GST)' })).toBe('Asia/Muscat')
      expect(resolveProspectTimezone({ timezone: 'GMT+3 (AST)' })).toBe('Asia/Qatar')
      expect(resolveProspectTimezone({ timezone: 'GMT+5:30 (IST)' })).toBe('Asia/Kolkata')
    })

    it('returns null when neither country nor timezone can be resolved (no silent UTC default)', () => {
      expect(resolveProspectTimezone({})).toBeNull()
      expect(resolveProspectTimezone({ country: '', timezone: '' })).toBeNull()
      expect(resolveProspectTimezone({ country: 'Not Available', timezone: 'Not Available' })).toBeNull()
    })
  })

  describe('getUtcOffset', () => {
    it('returns correct standard UTC offsets for non-DST regions', () => {
      expect(getUtcOffset('Asia/Manila')).toBe('UTC+08:00')
      expect(getUtcOffset('Asia/Muscat')).toBe('UTC+04:00')
      expect(getUtcOffset('Asia/Qatar')).toBe('UTC+03:00')
      expect(getUtcOffset('Asia/Kolkata')).toBe('UTC+05:30')
    })

    it('handles daylight saving time automatically for Europe and US', () => {
      // Winter date (January 15)
      const winterDate = new Date('2026-01-15T12:00:00Z')
      expect(getUtcOffset('Europe/Brussels', winterDate)).toBe('UTC+01:00')
      expect(getUtcOffset('Europe/Amsterdam', winterDate)).toBe('UTC+01:00')
      expect(getUtcOffset('America/New_York', winterDate)).toBe('UTC-05:00')

      // Summer date (July 15)
      const summerDate = new Date('2026-07-15T12:00:00Z')
      expect(getUtcOffset('Europe/Brussels', summerDate)).toBe('UTC+02:00')
      expect(getUtcOffset('Europe/Amsterdam', summerDate)).toBe('UTC+02:00')
      expect(getUtcOffset('America/New_York', summerDate)).toBe('UTC-04:00')
    })

    it('returns null for null or invalid timezone', () => {
      expect(getUtcOffset(null)).toBeNull()
      expect(getUtcOffset('')).toBeNull()
      expect(getUtcOffset('Invalid_Zone')).toBeNull()
    })
  })

  describe('formatProspectLocalTime', () => {
    it('returns unavailable display when timeZone is null or invalid', () => {
      const res = formatProspectLocalTime(null)
      expect(res.isAvailable).toBe(false)
      expect(res.display).toBe('Timezone unavailable')
    })

    it('calculates accurate time and greeting based on prospect local hour', () => {
      // 09:30 AM in Manila (Morning)
      const morningDate = new Date('2026-11-26T01:30:00Z') // 01:30 UTC = 09:30 Manila
      const morningRes = formatProspectLocalTime('Asia/Manila', morningDate)
      expect(morningRes.isAvailable).toBe(true)
      expect(morningRes.offset).toBe('UTC+08:00')
      expect(morningRes.greeting).toBe('Good morning')
      expect(morningRes.display).toContain('UTC+08:00')
      expect(morningRes.display).toContain('Good morning')

      // 02:30 PM in Qatar (Afternoon)
      const afternoonDate = new Date('2026-11-26T11:30:00Z') // 11:30 UTC = 14:30 Qatar
      const afternoonRes = formatProspectLocalTime('Asia/Qatar', afternoonDate)
      expect(afternoonRes.isAvailable).toBe(true)
      expect(afternoonRes.offset).toBe('UTC+03:00')
      expect(afternoonRes.greeting).toBe('Good afternoon')
      expect(afternoonRes.display).toContain('UTC+03:00')
      expect(afternoonRes.display).toContain('Good afternoon')

      // 07:30 PM in Muscat (Evening)
      const eveningDate = new Date('2026-11-26T15:30:00Z') // 15:30 UTC = 19:30 Muscat
      const eveningRes = formatProspectLocalTime('Asia/Muscat', eveningDate)
      expect(eveningRes.isAvailable).toBe(true)
      expect(eveningRes.offset).toBe('UTC+04:00')
      expect(eveningRes.greeting).toBe('Good evening')
      expect(eveningRes.display).toContain('UTC+04:00')
      expect(eveningRes.display).toContain('Good evening')
    })
  })

  describe('formatProspectTimezoneDisplay', () => {
    it('returns Timezone unavailable when timezone is missing', () => {
      expect(formatProspectTimezoneDisplay(null)).toBe('Timezone unavailable')
      expect(formatProspectTimezoneDisplay('')).toBe('Timezone unavailable')
    })

    it('formats display with IANA timezone and UTC offset', () => {
      expect(formatProspectTimezoneDisplay('Asia/Manila')).toBe('Asia/Manila (UTC+08:00)')
      expect(formatProspectTimezoneDisplay('Asia/Qatar')).toBe('Asia/Qatar (UTC+03:00)')
      expect(formatProspectTimezoneDisplay('Asia/Muscat')).toBe('Asia/Muscat (UTC+04:00)')
      expect(formatProspectTimezoneDisplay('Europe/Brussels')).toBe('Europe/Brussels (UTC+01:00)')
      expect(formatProspectTimezoneDisplay('Europe/Amsterdam')).toBe('Europe/Amsterdam (UTC+01:00)')
    })
  })

  describe('Production Bug Regression: Haytham Abdeen (Qatar) and similar prospects', () => {
    it('accurately resolves Qatar with raw GMT+3 and raw_timezone', () => {
      // Case 1: MyTasks payload with raw_timezone = 'Asia/Qatar' and timezone = 'GMT+3'
      const tz1 = resolveProspectTimezone({
        country: 'Qatar',
        timezone: 'GMT+3',
        rawTimezone: 'Asia/Qatar',
      })
      expect(tz1).toBe('Asia/Qatar')
      expect(formatProspectTimezoneDisplay(tz1)).toBe('Asia/Qatar (UTC+03:00)')

      // Case 2: Only country = 'Qatar' and timezone = 'GMT+3' (no raw_timezone)
      const tz2 = resolveProspectTimezone({
        country: 'Qatar',
        timezone: 'GMT+3',
      })
      expect(tz2).toBe('Asia/Qatar')
      expect(formatProspectTimezoneDisplay(tz2)).toBe('Asia/Qatar (UTC+03:00)')

      // CRITICAL: Must NEVER resolve to Europe/London
      expect(tz1).not.toBe('Europe/London')
      expect(tz2).not.toBe('Europe/London')
    })

    it('accurately resolves Oman with raw GMT+4 and raw_timezone', () => {
      const tz = resolveProspectTimezone({
        country: 'Oman',
        timezone: 'GMT+4',
      })
      expect(tz).toBe('Asia/Muscat')
      expect(formatProspectTimezoneDisplay(tz)).toBe('Asia/Muscat (UTC+04:00)')
      expect(tz).not.toBe('Europe/London')
    })

    it('accurately resolves Philippines with raw GMT+8 and raw_timezone', () => {
      const tz = resolveProspectTimezone({
        country: 'Philippines',
        timezone: 'GMT+8',
      })
      expect(tz).toBe('Asia/Manila')
      expect(formatProspectTimezoneDisplay(tz)).toBe('Asia/Manila (UTC+08:00)')
      expect(tz).not.toBe('Europe/London')
    })

    it('does NOT interpret raw offsets like GMT+3, GMT+4, GMT+8 as Europe/London or UTC+00:00 when country is missing', () => {
      // Must return null, not Europe/London
      expect(resolveProspectTimezone({ timezone: 'GMT+3' })).toBeNull()
      expect(resolveProspectTimezone({ timezone: 'GMT+4' })).toBeNull()
      expect(resolveProspectTimezone({ timezone: 'GMT+8' })).toBeNull()
    })
  })
})
