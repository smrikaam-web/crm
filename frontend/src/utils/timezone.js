/**
 * Timezone resolution and local time formatting utility.
 * Mirrors the country-to-timezone resolution of CRM Daily Allocation and provides
 * DST-aware, IANA-compliant local time calculations.
 */

export const COUNTRY_TIMEZONE_MAP = {
  // Asia & Middle East
  india: 'Asia/Kolkata',
  in: 'Asia/Kolkata',
  singapore: 'Asia/Singapore',
  sg: 'Asia/Singapore',
  malaysia: 'Asia/Kuala_Lumpur',
  my: 'Asia/Kuala_Lumpur',
  philippines: 'Asia/Manila',
  ph: 'Asia/Manila',
  qatar: 'Asia/Qatar',
  qa: 'Asia/Qatar',
  oman: 'Asia/Muscat',
  om: 'Asia/Muscat',
  'united arab emirates': 'Asia/Dubai',
  uae: 'Asia/Dubai',
  ae: 'Asia/Dubai',
  'saudi arabia': 'Asia/Riyadh',
  sa: 'Asia/Riyadh',
  kuwait: 'Asia/Kuwait',
  kw: 'Asia/Kuwait',
  bahrain: 'Asia/Bahrain',
  bh: 'Asia/Bahrain',
  japan: 'Asia/Tokyo',
  jp: 'Asia/Tokyo',
  china: 'Asia/Shanghai',
  cn: 'Asia/Shanghai',
  'hong kong': 'Asia/Hong_Kong',
  hk: 'Asia/Hong_Kong',
  taiwan: 'Asia/Taipei',
  tw: 'Asia/Taipei',
  'south korea': 'Asia/Seoul',
  korea: 'Asia/Seoul',
  kr: 'Asia/Seoul',
  indonesia: 'Asia/Jakarta',
  id: 'Asia/Jakarta',
  thailand: 'Asia/Bangkok',
  th: 'Asia/Bangkok',
  vietnam: 'Asia/Ho_Chi_Minh',
  'viet nam': 'Asia/Ho_Chi_Minh',
  vn: 'Asia/Ho_Chi_Minh',
  bangladesh: 'Asia/Dhaka',
  bd: 'Asia/Dhaka',
  pakistan: 'Asia/Karachi',
  pk: 'Asia/Karachi',
  'sri lanka': 'Asia/Colombo',
  lk: 'Asia/Colombo',
  nepal: 'Asia/Kathmandu',
  np: 'Asia/Kathmandu',
  israel: 'Asia/Jerusalem',
  il: 'Asia/Jerusalem',

  // Europe
  'united kingdom': 'Europe/London',
  uk: 'Europe/London',
  gb: 'Europe/London',
  'great britain': 'Europe/London',
  ireland: 'Europe/Dublin',
  ie: 'Europe/Dublin',
  belgium: 'Europe/Brussels',
  be: 'Europe/Brussels',
  netherlands: 'Europe/Amsterdam',
  nl: 'Europe/Amsterdam',
  holland: 'Europe/Amsterdam',
  germany: 'Europe/Berlin',
  de: 'Europe/Berlin',
  france: 'Europe/Paris',
  fr: 'Europe/Paris',
  austria: 'Europe/Vienna',
  at: 'Europe/Vienna',
  switzerland: 'Europe/Zurich',
  ch: 'Europe/Zurich',
  italy: 'Europe/Rome',
  it: 'Europe/Rome',
  spain: 'Europe/Madrid',
  es: 'Europe/Madrid',
  portugal: 'Europe/Lisbon',
  pt: 'Europe/Lisbon',
  sweden: 'Europe/Stockholm',
  se: 'Europe/Stockholm',
  norway: 'Europe/Oslo',
  no: 'Europe/Oslo',
  denmark: 'Europe/Copenhagen',
  dk: 'Europe/Copenhagen',
  finland: 'Europe/Helsinki',
  fi: 'Europe/Helsinki',
  poland: 'Europe/Warsaw',
  pl: 'Europe/Warsaw',
  greece: 'Europe/Athens',
  gr: 'Europe/Athens',
  turkey: 'Europe/Istanbul',
  türkiye: 'Europe/Istanbul',
  tr: 'Europe/Istanbul',
  russia: 'Europe/Moscow',
  ru: 'Europe/Moscow',

  // Americas
  'united states': 'America/New_York',
  'united states of america': 'America/New_York',
  usa: 'America/New_York',
  us: 'America/New_York',
  canada: 'America/Toronto',
  ca: 'America/Toronto',
  mexico: 'America/Mexico_City',
  mx: 'America/Mexico_City',
  brazil: 'America/Sao_Paulo',
  brasil: 'America/Sao_Paulo',
  br: 'America/Sao_Paulo',
  argentina: 'America/Argentina/Buenos_Aires',
  ar: 'America/Argentina/Buenos_Aires',
  chile: 'America/Santiago',
  cl: 'America/Santiago',
  colombia: 'America/Bogota',
  co: 'America/Bogota',
  peru: 'America/Lima',
  pe: 'America/Lima',

  // Oceania & Africa
  australia: 'Australia/Sydney',
  au: 'Australia/Sydney',
  'new zealand': 'Pacific/Auckland',
  nz: 'Pacific/Auckland',
  'south africa': 'Africa/Johannesburg',
  za: 'Africa/Johannesburg',
  egypt: 'Africa/Cairo',
  eg: 'Africa/Cairo',
  nigeria: 'Africa/Lagos',
  ng: 'Africa/Lagos',
  kenya: 'Africa/Nairobi',
  ke: 'Africa/Nairobi',
}

// Regional US timezones mapping for prospects with explicit regional cues
const US_REGIONAL_MAP = {
  pst: 'America/Los_Angeles',
  pdt: 'America/Los_Angeles',
  'pacific standard time': 'America/Los_Angeles',
  'pacific daylight time': 'America/Los_Angeles',
  'america/los_angeles': 'America/Los_Angeles',
  california: 'America/Los_Angeles',
  washington: 'America/Los_Angeles',
  oregon: 'America/Los_Angeles',
  nevada: 'America/Los_Angeles',

  mst: 'America/Denver',
  mdt: 'America/Denver',
  'mountain standard time': 'America/Denver',
  'mountain daylight time': 'America/Denver',
  'america/denver': 'America/Denver',
  colorado: 'America/Denver',
  utah: 'America/Denver',
  arizona: 'America/Phoenix',
  'america/phoenix': 'America/Phoenix',

  cst: 'America/Chicago',
  cdt: 'America/Chicago',
  'central standard time': 'America/Chicago',
  'central daylight time': 'America/Chicago',
  'america/chicago': 'America/Chicago',
  texas: 'America/Chicago',
  illinois: 'America/Chicago',
  minnesota: 'America/Chicago',

  est: 'America/New_York',
  edt: 'America/New_York',
  'eastern standard time': 'America/New_York',
  'eastern daylight time': 'America/New_York',
  'america/new_york': 'America/New_York',
  florida: 'America/New_York',
  georgia: 'America/New_York',
  'north carolina': 'America/New_York',
}

// Map common time zone abbreviations to primary IANA zones
const ABBR_TO_IANA = {
  pht: 'Asia/Manila',
  gst: 'Asia/Muscat',
  ast: 'Asia/Qatar',
  ist: 'Asia/Kolkata',
  sgt: 'Asia/Singapore',
  myt: 'Asia/Kuala_Lumpur',
  jst: 'Asia/Tokyo',
  kst: 'Asia/Seoul',
  ict: 'Asia/Bangkok',
  wib: 'Asia/Jakarta',
  sast: 'Africa/Johannesburg',
  aest: 'Australia/Sydney',
  aedt: 'Australia/Sydney',
  nzst: 'Pacific/Auckland',
  nzdt: 'Pacific/Auckland',
  cet: 'Europe/Brussels',
  cest: 'Europe/Brussels',
  bst: 'Europe/London',
  est: 'America/New_York',
  edt: 'America/New_York',
  cst: 'America/Chicago',
  cdt: 'America/Chicago',
  mst: 'America/Denver',
  mdt: 'America/Denver',
  pst: 'America/Los_Angeles',
  pdt: 'America/Los_Angeles',
}

/**
 * Validates whether a given string is a valid IANA timezone identifier supported by the runtime.
 * @param {string} tz
 * @returns {boolean}
 */
export function isValidIanaTimezone(tz) {
  if (!tz || typeof tz !== 'string') return false
  const trimmed = tz.trim()
  if (!trimmed || trimmed.toLowerCase() === 'not available' || trimmed === '—') {
    return false
  }
  // Exclude raw offset strings like GMT+8 or UTC+03:00 from being treated as IANA zone names
  if (/^(GMT|UTC)[+-]?\d/i.test(trimmed)) {
    return false
  }
  // Exclude 3-4 letter abbreviations (like CST, EST, PST) except UTC so they can be mapped to canonical Region/City IANA zones
  if (/^[A-Za-z]{3,4}$/.test(trimmed) && trimmed.toUpperCase() !== 'UTC') {
    return false
  }
  try {
    Intl.DateTimeFormat(undefined, { timeZone: trimmed })
    return true
  } catch (e) {
    return false
  }
}

/**
 * Derive primary IANA timezone identifier from a country name or ISO-2 code.
 * @param {string} country
 * @returns {string|null}
 */
export function getTimezoneForCountry(country) {
  if (!country || typeof country !== 'string') return null
  const cleaned = country.trim().toLowerCase()
  if (!cleaned || cleaned === 'not available' || cleaned === '—') return null

  // 1. Direct key match
  if (COUNTRY_TIMEZONE_MAP[cleaned]) {
    return COUNTRY_TIMEZONE_MAP[cleaned]
  }

  // 2. Substring matching for multi-word or variant names
  for (const [key, tz] of Object.entries(COUNTRY_TIMEZONE_MAP)) {
    if (key.length > 2 && (cleaned.includes(key) || key.includes(cleaned))) {
      return tz
    }
  }

  return null
}

/**
 * Extracts abbreviation from a label like 'GMT+8 (PHT)' and maps to IANA timezone.
 * @param {string} tzStr
 * @returns {string|null}
 */
export function parseOffsetOrAbbrToIana(tzStr) {
  if (!tzStr || typeof tzStr !== 'string') return null
  const trimmed = tzStr.trim()

  // Match pattern like 'GMT+8 (PHT)' -> capture 'PHT'
  const match = trimmed.match(/\(([^)]+)\)/)
  if (match && match[1]) {
    const abbr = match[1].trim().toLowerCase()
    if (ABBR_TO_IANA[abbr]) {
      return ABBR_TO_IANA[abbr]
    }
  }

  const rawLower = trimmed.toLowerCase()
  if (ABBR_TO_IANA[rawLower]) {
    return ABBR_TO_IANA[rawLower]
  }

  return null
}

/**
 * Resolves the prospect's actual IANA timezone.
 * Hierarchy:
 * 1. rawTimezone if it is a valid IANA identifier (e.g. 'Asia/Qatar', 'Asia/Manila').
 * 2. customTimezone / timezone if it is already a valid IANA identifier.
 * 3. Country-based timezone resolution using COUNTRY_TIMEZONE_MAP.
 *    For US, checks regional hints if available.
 * 4. Extracted abbreviation from formatted string (e.g. 'PHT' in 'GMT+8 (PHT)').
 * 5. Returns null if timezone cannot be determined (NO silent UTC or browser fallback).
 *
 * @param {Object} options
 * @param {string} [options.timezone] - Formatted or raw timezone field
 * @param {string} [options.rawTimezone] - Raw IANA timezone from backend task query
 * @param {string} [options.customTimezone] - Explicit custom_timezone from Contact doc
 * @param {string} [options.country] - Prospect country
 * @returns {string|null} IANA timezone identifier e.g. 'Asia/Manila' or null
 */
export function resolveProspectTimezone({
  timezone = '',
  rawTimezone = '',
  customTimezone = '',
  country = '',
} = {}) {
  // 1. Check rawTimezone
  if (isValidIanaTimezone(rawTimezone)) {
    return rawTimezone.trim()
  }

  // 2. Check customTimezone
  if (isValidIanaTimezone(customTimezone)) {
    return customTimezone.trim()
  }

  // 3. Check timezone field
  if (isValidIanaTimezone(timezone)) {
    return timezone.trim()
  }

  // 4. Resolve via Country
  const countryTz = getTimezoneForCountry(country)
  if (countryTz) {
    // If country is US, check for regional clues in timezone/customTimezone
    const cleanCountry = (country || '').trim().toLowerCase()
    if (['united states', 'usa', 'us', 'united states of america'].includes(cleanCountry)) {
      const hint = `${timezone} ${customTimezone}`.toLowerCase()
      for (const [key, mappedTz] of Object.entries(US_REGIONAL_MAP)) {
        if (hint.includes(key)) {
          return mappedTz
        }
      }
    }
    return countryTz
  }

  // 5. Try parsing from abbreviation in timezone or customTimezone (e.g. 'GMT+8 (PHT)')
  const fromTzAbbr = parseOffsetOrAbbrToIana(timezone)
  if (fromTzAbbr) {
    return fromTzAbbr
  }
  const fromCustomAbbr = parseOffsetOrAbbrToIana(customTimezone)
  if (fromCustomAbbr) {
    return fromCustomAbbr
  }

  // Unresolvable: return null (caller will handle fallback message)
  return null
}

/**
 * Calculates the exact DST-aware UTC offset for a given IANA timezone and date.
 * @param {string} timeZone - e.g. 'Asia/Manila', 'Europe/Brussels'
 * @param {Date} [date] - Defaults to new Date()
 * @returns {string|null} e.g. 'UTC+08:00', 'UTC+04:00', 'UTC+01:00' or null
 */
export function getUtcOffset(timeZone, date = new Date()) {
  if (!timeZone || !isValidIanaTimezone(timeZone)) return null

  try {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      timeZoneName: 'shortOffset',
    }).formatToParts(date)
    const tzPart = parts.find((p) => p.type === 'timeZoneName')
    if (tzPart?.value) {
      if (tzPart.value === 'GMT' || tzPart.value === 'UTC') {
        return 'UTC+00:00'
      }
      const raw = tzPart.value.replace('GMT', 'UTC')
      const match = raw.match(/UTC([+-])(\d+)(?::(\d+))?/)
      if (match) {
        const sign = match[1]
        const h = match[2].padStart(2, '0')
        const m = (match[3] || '00').padStart(2, '0')
        return `UTC${sign}${h}:${m}`
      }
      return raw
    }
  } catch (e) {}

  // Fallback offset calculation via difference in minutes
  try {
    const now = date || new Date()
    const utcDate = new Date(now.toLocaleString('en-US', { timeZone: 'UTC' }))
    const tzDate = new Date(now.toLocaleString('en-US', { timeZone }))
    const diffMinutes = Math.round((tzDate.getTime() - utcDate.getTime()) / 60000)
    const sign = diffMinutes >= 0 ? '+' : '-'
    const absMinutes = Math.abs(diffMinutes)
    const hours = Math.floor(absMinutes / 60).toString().padStart(2, '0')
    const mins = (absMinutes % 60).toString().padStart(2, '0')
    return `UTC${sign}${hours}:${mins}`
  } catch (e) {}

  return null
}

/**
 * Formats the prospect's local time, live UTC offset, and greeting.
 * @param {string|null} timeZone - IANA timezone identifier
 * @param {Date} [date] - Current date/time
 * @returns {{ time: string, offset: string, greeting: string, display: string, isAvailable: boolean }}
 */
export function formatProspectLocalTime(timeZone, date = new Date()) {
  if (!timeZone || !isValidIanaTimezone(timeZone)) {
    return {
      time: '',
      offset: '',
      greeting: '',
      display: 'Timezone unavailable',
      isAvailable: false,
    }
  }

  const now = date || new Date()

  try {
    const timeFormatter = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
    const timeFormatted = timeFormatter.format(now)

    const hourFormatter = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      hourCycle: 'h23',
    })
    const hour = parseInt(hourFormatter.format(now), 10)

    let greeting = 'Good morning'
    if (hour >= 5 && hour < 12) {
      greeting = 'Good morning'
    } else if (hour >= 12 && hour < 17) {
      greeting = 'Good afternoon'
    } else if (hour >= 17 && hour < 21) {
      greeting = 'Good evening'
    } else {
      greeting = 'Good night'
    }

    const offset = getUtcOffset(timeZone, now) || 'UTC+00:00'

    return {
      time: timeFormatted,
      offset,
      greeting,
      display: `${timeFormatted} · ${offset} · ${greeting}`,
      isAvailable: true,
    }
  } catch (e) {
    return {
      time: '',
      offset: '',
      greeting: '',
      display: 'Timezone unavailable',
      isAvailable: false,
    }
  }
}

/**
 * Formats the timezone display row in the prospect contact info card.
 * @param {string|null} timeZone - IANA timezone identifier
 * @param {string} [country] - Prospect country name
 * @param {Date} [date] - Current date
 * @returns {string} e.g. 'Asia/Manila (UTC+08:00)' or 'Timezone unavailable'
 */
export function formatProspectTimezoneDisplay(timeZone, country = '', date = new Date()) {
  if (!timeZone || !isValidIanaTimezone(timeZone)) {
    return 'Timezone unavailable'
  }
  const offset = getUtcOffset(timeZone, date)
  if (offset) {
    return `${timeZone} (${offset})`
  }
  return timeZone
}
