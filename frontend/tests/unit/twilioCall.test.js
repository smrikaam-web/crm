import { describe, it, expect } from 'vitest'
import {
  validateTokenResponse,
  mapTwilioSignalingStatus,
  extractCallErrorMessage,
  canInitiateCall,
  sanitizePhoneNumber,
  DIALPAD_KEYS,
  formatCallerIdLabel,
  validateCallerIdsResponse,
  selectDefaultCallerId,
} from '@/utils/twilioCall'

describe('validateTokenResponse', () => {
  it('returns false for null or undefined input', () => {
    expect(validateTokenResponse(null)).toEqual({
      ok: false,
      error: 'empty_response',
      message: 'Invalid response from telephony service.',
    })
    expect(validateTokenResponse(undefined)).toEqual({
      ok: false,
      error: 'empty_response',
      message: 'Invalid response from telephony service.',
    })
  })

  it('handles caller_phone_identity_missing correctly with fallback message', () => {
    const res = validateTokenResponse({
      ok: false,
      error: 'caller_phone_identity_missing',
    })
    expect(res.ok).toBe(false)
    expect(res.error).toBe('caller_phone_identity_missing')
    expect(res.message).toBe(
      'Your account is not configured with a Twilio phone number. Please contact your administrator.',
    )
  })

  it('preserves backend detail message if provided for missing caller phone', () => {
    const res = validateTokenResponse({
      ok: false,
      error: 'caller_phone_identity_missing',
      detail: 'Phone number is not mapped to the caller',
    })
    expect(res.ok).toBe(false)
    expect(res.error).toBe('caller_phone_identity_missing')
    expect(res.message).toBe('Phone number is not mapped to the caller')
  })

  it('handles twilio_not_configured with appropriate administrator guidance', () => {
    const res = validateTokenResponse({
      ok: false,
      error: 'twilio_not_configured',
    })
    expect(res.ok).toBe(false)
    expect(res.error).toBe('twilio_not_configured')
    expect(res.message).toBe(
      'Twilio configuration is missing. Please contact your administrator.',
    )
  })

  it('returns ok: true and extracts token when token is present', () => {
    const res = validateTokenResponse({
      ok: true,
      token: 'jwt.mock.token.123',
    })
    expect(res.ok).toBe(true)
    expect(res.token).toBe('jwt.mock.token.123')
  })

  it('handles missing token when ok is not explicitly false', () => {
    const res = validateTokenResponse({})
    expect(res.ok).toBe(false)
    expect(res.error).toBe('token_generation_failed')
  })
})

describe('mapTwilioSignalingStatus', () => {
  it('maps initiating and ringing statuses', () => {
    expect(mapTwilioSignalingStatus('queued')).toBe('initiating')
    expect(mapTwilioSignalingStatus('initiated')).toBe('initiating')
    expect(mapTwilioSignalingStatus('ringing')).toBe('ringing')
    expect(mapTwilioSignalingStatus('early-media')).toBe('ringing')
  })

  it('maps connected and in-progress statuses', () => {
    expect(mapTwilioSignalingStatus('in-progress')).toBe('connected')
    expect(mapTwilioSignalingStatus('inprogress')).toBe('connected')
    expect(mapTwilioSignalingStatus('answered')).toBe('connected')
  })

  it('maps terminal statuses', () => {
    expect(mapTwilioSignalingStatus('busy')).toBe('busy')
    expect(mapTwilioSignalingStatus('no-answer')).toBe('no-answer')
    expect(mapTwilioSignalingStatus('failed')).toBe('failed')
    expect(mapTwilioSignalingStatus('canceled')).toBe('failed')
    expect(mapTwilioSignalingStatus('completed')).toBe('completed')
  })

  it('returns unknown for unrecognized status', () => {
    expect(mapTwilioSignalingStatus('xyz_unknown')).toBe('unknown')
    expect(mapTwilioSignalingStatus('')).toBe('unknown')
    expect(mapTwilioSignalingStatus(null)).toBe('unknown')
  })
})

describe('extractCallErrorMessage', () => {
  it('formats microphone permission denial clearly', () => {
    const error = new Error('Permission denied by user')
    error.name = 'NotAllowedError'
    expect(extractCallErrorMessage(error)).toBe(
      'Microphone access was denied. Please allow microphone permissions in your browser.',
    )
  })

  it('formats Twilio gateway connection failure', () => {
    const error = { code: 31005, message: 'Connection to gateway failed' }
    expect(extractCallErrorMessage(error)).toBe(
      'Unable to connect to Twilio voice servers. Please check your network connection.',
    )
  })

  it('formats invalid phone number format error', () => {
    const error = { code: 21210, message: "The 'To' number is not a valid phone number" }
    expect(extractCallErrorMessage(error)).toBe(
      'The recipient phone number is invalid. Please verify the international format (e.g. +1234567890).',
    )
  })

  it('formats unready Twilio device error', () => {
    const error = new Error('Twilio device not ready')
    expect(extractCallErrorMessage(error)).toBe(
      'Twilio calling device is not ready. Please verify your phone mapping and reload.',
    )
  })

  it('falls back to error message or default text', () => {
    expect(extractCallErrorMessage(new Error('Custom error'))).toBe('Custom error')
    expect(extractCallErrorMessage(null)).toBe('Call could not be completed.')
  })
})

describe('canInitiateCall', () => {
  it('blocks call if phone number is missing or empty', () => {
    expect(canInitiateCall({ mobileNumber: '' })).toEqual({
      canCall: false,
      reason: 'missing_number',
    })
    expect(canInitiateCall({ mobileNumber: '   ' })).toEqual({
      canCall: false,
      reason: 'missing_number',
    })
  })

  it('blocks call if another call is currently initiating', () => {
    expect(
      canInitiateCall({
        mobileNumber: '+1234567890',
        isMakingCall: true,
        isCallActive: false,
      }),
    ).toEqual({
      canCall: false,
      reason: 'call_already_initiating',
    })
  })

  it('blocks call if a call is already active or in progress', () => {
    expect(
      canInitiateCall({
        mobileNumber: '+1234567890',
        isMakingCall: false,
        isCallActive: true,
      }),
    ).toEqual({
      canCall: false,
      reason: 'call_already_active',
    })
  })

  it('blocks call if phone number contains fewer than 3 digits without dtmf', () => {
    expect(canInitiateCall({ mobileNumber: '12' })).toEqual({
      canCall: false,
      reason: 'invalid_number',
    })
  })

  it('allows call when number is provided and no calls are active or initiating', () => {
    expect(
      canInitiateCall({
        mobileNumber: '+1234567890',
        isMakingCall: false,
        isCallActive: false,
      }),
    ).toEqual({
      canCall: true,
    })
  })
})

describe('sanitizePhoneNumber', () => {
  it('strips parentheses, spaces and hyphens while preserving international +', () => {
    expect(sanitizePhoneNumber('+1 (555) 123-4567')).toBe('+15551234567')
    expect(sanitizePhoneNumber('+91 98765-43210')).toBe('+919876543210')
  })

  it('preserves clean digits and DTMF characters', () => {
    expect(sanitizePhoneNumber('9876543210')).toBe('9876543210')
    expect(sanitizePhoneNumber('*123#')).toBe('*123#')
  })

  it('handles empty or non-string inputs gracefully', () => {
    expect(sanitizePhoneNumber('')).toBe('')
    expect(sanitizePhoneNumber(null)).toBe('')
    expect(sanitizePhoneNumber(undefined)).toBe('')
  })
})

describe('DIALPAD_KEYS', () => {
  it('contains standard 12 dial pad keys', () => {
    expect(DIALPAD_KEYS).toHaveLength(12)
    const digits = DIALPAD_KEYS.map((k) => k.digit)
    expect(digits).toEqual(['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'])
  })
})

describe('formatCallerIdLabel', () => {
  it('formats US numbers with country code and name', () => {
    expect(formatCallerIdLabel('+12025550143')).toBe('US United States • +12025550143')
  })

  it('formats US numbers with custom friendly name', () => {
    expect(formatCallerIdLabel('+12025550143', 'Sales Line')).toBe(
      'US United States (Sales Line) • +12025550143',
    )
  })

  it('formats UK and India numbers with appropriate country info', () => {
    expect(formatCallerIdLabel('+447412097737')).toBe('GB United Kingdom • +447412097737')
    expect(formatCallerIdLabel('+919876543210')).toBe('IN India • +919876543210')
  })

  it('handles numbers without known country prefix', () => {
    expect(formatCallerIdLabel('+8881234567')).toBe('+8881234567')
    expect(formatCallerIdLabel('+8881234567', 'Global Toll-Free')).toBe('Global Toll-Free • +8881234567')
  })

  it('returns empty string for null or empty number', () => {
    expect(formatCallerIdLabel('')).toBe('')
    expect(formatCallerIdLabel(null)).toBe('')
  })
})

describe('validateCallerIdsResponse', () => {
  it('returns error when response is null or invalid', () => {
    expect(validateCallerIdsResponse(null)).toEqual({
      ok: false,
      callerIds: [],
      error: 'empty_response',
      message: 'Invalid response from telephony service.',
    })
  })

  it('handles ok: false from backend with error message', () => {
    const res = validateCallerIdsResponse({
      ok: false,
      error: 'twilio_disabled',
      message: 'Twilio integration is not enabled.',
    })
    expect(res.ok).toBe(false)
    expect(res.callerIds).toEqual([])
    expect(res.error).toBe('twilio_disabled')
    expect(res.message).toBe('Twilio integration is not enabled.')
  })

  it('handles frappe.call response wrapped in message property', () => {
    const res = validateCallerIdsResponse({
      message: {
        ok: true,
        numbers: [
          { number: '+12025550143', label: 'US United States • +12025550143' },
        ],
      },
    })
    expect(res.ok).toBe(true)
    expect(res.callerIds).toHaveLength(1)
    expect(res.callerIds[0].number).toBe('+12025550143')
  })

  it('filters out empty or duplicate numbers', () => {
    const res = validateCallerIdsResponse({
      ok: true,
      numbers: [
        '+12025550143',
        '+12025550143', // duplicate
        '', // empty
        null, // null
        { number: '+19388370825', friendly_name: 'Alabama Office' },
      ],
    })
    expect(res.ok).toBe(true)
    expect(res.callerIds).toHaveLength(2)
    expect(res.callerIds[0].number).toBe('+12025550143')
    expect(res.callerIds[1].number).toBe('+19388370825')
    expect(res.callerIds[1].friendly_name).toBe('Alabama Office')
  })
})

describe('selectDefaultCallerId', () => {
  const sampleCallerIds = [
    { number: '+12025550143', label: 'US Main • +12025550143' },
    { number: '+19388370825', label: 'US Direct • +19388370825' },
  ]

  it('selects preferred number when present in callerIds', () => {
    const selected = selectDefaultCallerId(sampleCallerIds, '+19388370825')
    expect(selected).toEqual(sampleCallerIds[1])
  })

  it('selects preferred number ignoring whitespace differences', () => {
    const selected = selectDefaultCallerId(sampleCallerIds, '+1 938 837 0825')
    expect(selected).toEqual(sampleCallerIds[1])
  })

  it('defaults to first caller ID if preferred number is not in list', () => {
    const selected = selectDefaultCallerId(sampleCallerIds, '+447412097737')
    expect(selected).toEqual(sampleCallerIds[0])
  })

  it('defaults to first caller ID when no preferred number is specified', () => {
    const selected = selectDefaultCallerId(sampleCallerIds)
    expect(selected).toEqual(sampleCallerIds[0])
  })

  it('returns null when callerIds array is empty or invalid', () => {
    expect(selectDefaultCallerId([])).toBeNull()
    expect(selectDefaultCallerId(null)).toBeNull()
  })
})
