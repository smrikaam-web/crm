/**
 * Pure utility functions for Twilio calling flow:
 * - Access token response validation
 * - Signaling and message status mapping
 * - Error message extraction and user-friendly formatting
 * - Outgoing call initiation validation
 */

/**
 * Validates the response returned by `crm.integrations.twilio.api.generate_access_token`.
 * @param {Object} data
 * @returns {{ ok: boolean, token?: string, error?: string, message?: string }}
 */
export function validateTokenResponse(data) {
  if (!data || typeof data !== 'object') {
    return {
      ok: false,
      error: 'empty_response',
      message: 'Invalid response from telephony service.',
    }
  }

  if (data.ok === false || !data.token) {
    const error = data.error || 'token_generation_failed'
    let message = data.detail || data.message

    if (!message) {
      if (error === 'caller_phone_identity_missing') {
        message =
          'Your account is not configured with a Twilio phone number. Please contact your administrator.'
      } else if (error === 'twilio_not_configured') {
        message =
          'Twilio configuration is missing. Please contact your administrator.'
      } else {
        message = 'Failed to generate Twilio access token. Please verify Twilio settings.'
      }
    }

    return {
      ok: false,
      error,
      message,
    }
  }

  return {
    ok: true,
    token: data.token,
  }
}

/**
 * Maps incoming Twilio status strings (from Voice SDK or status callbacks)
 * to standard normalized call states.
 * @param {string} rawStatus
 * @returns {'initiating'|'ringing'|'connected'|'busy'|'no-answer'|'failed'|'completed'|'unknown'}
 */
export function mapTwilioSignalingStatus(rawStatus) {
  if (!rawStatus || typeof rawStatus !== 'string') return 'unknown'
  const normalized = rawStatus.trim().toLowerCase().replace(/_/g, '-')

  switch (normalized) {
    case 'queued':
    case 'initiated':
    case 'initiating':
      return 'initiating'
    case 'ringing':
    case 'early-media':
      return 'ringing'
    case 'in-progress':
    case 'inprogress':
    case 'answered':
    case 'connected':
      return 'connected'
    case 'busy':
      return 'busy'
    case 'no-answer':
    case 'noanswer':
      return 'no-answer'
    case 'failed':
    case 'canceled':
    case 'cancelled':
      return 'failed'
    case 'completed':
    case 'disconnected':
      return 'completed'
    default:
      return 'unknown'
  }
}

/**
 * Extracts a friendly, actionable error message from Twilio Voice SDK or browser WebRTC errors.
 * @param {any} error
 * @returns {string}
 */
export function extractCallErrorMessage(error) {
  if (!error) return 'Call could not be completed.'

  const name = error?.name || ''
  const message = error?.message || (typeof error === 'string' ? error : '')
  const code = error?.code

  // Microphone permission errors
  if (
    name === 'NotAllowedError' ||
    name === 'PermissionDeniedError' ||
    /permission denied/i.test(message) ||
    /microphone/i.test(message)
  ) {
    return 'Microphone access was denied. Please allow microphone permissions in your browser.'
  }

  // Network / Gateway connection errors
  if (code === 31005 || /connection error/i.test(message) || /gateway/i.test(message)) {
    return 'Unable to connect to Twilio voice servers. Please check your network connection.'
  }

  // Invalid phone number format
  if (code === 21210 || /valid phone number/i.test(message)) {
    return 'The recipient phone number is invalid. Please verify the international format (e.g. +1234567890).'
  }

  // Twilio Device not ready
  if (/device not ready/i.test(message) || /not registered/i.test(message)) {
    return 'Twilio calling device is not ready. Please verify your phone mapping and reload.'
  }

  return message || error?.detail || 'Call could not be completed.'
}

/**
 * Standard dial pad keys with alphanumeric labels for DTMF and outgoing dialing.
 */
export const DIALPAD_KEYS = [
  { digit: '1', sub: '' },
  { digit: '2', sub: 'ABC' },
  { digit: '3', sub: 'DEF' },
  { digit: '4', sub: 'GHI' },
  { digit: '5', sub: 'JKL' },
  { digit: '6', sub: 'MNO' },
  { digit: '7', sub: 'PQRS' },
  { digit: '8', sub: 'TUV' },
  { digit: '9', sub: 'WXYZ' },
  { digit: '*', sub: '' },
  { digit: '0', sub: '+' },
  { digit: '#', sub: '' },
]

/**
 * Sanitizes phone numbers for telephony providers, preserving leading + and numeric/DTMF chars.
 * @param {string} number
 * @returns {string}
 */
export function sanitizePhoneNumber(number) {
  if (!number) return ''
  const trimmed = String(number).trim()
  const hasPlus = trimmed.startsWith('+')
  const cleaned = trimmed.replace(/[^\d*#]/g, '')
  return hasPlus ? `+${cleaned}` : cleaned
}

/**
 * Validates whether an outgoing call can be safely initiated.
 * @param {{ isMakingCall?: boolean, isCallActive?: boolean, mobileNumber?: string }} params
 * @returns {{ canCall: boolean, reason?: string }}
 */
export function canInitiateCall({ isMakingCall, isCallActive, mobileNumber } = {}) {
  const cleaned = mobileNumber ? String(mobileNumber).trim() : ''
  if (!cleaned) {
    return { canCall: false, reason: 'missing_number' }
  }
  const digitsOnly = cleaned.replace(/\D/g, '')
  if (digitsOnly.length < 3 && !cleaned.includes('*') && !cleaned.includes('#')) {
    return { canCall: false, reason: 'invalid_number' }
  }
  if (isMakingCall) {
    return { canCall: false, reason: 'call_already_initiating' }
  }
  if (isCallActive) {
    return { canCall: false, reason: 'call_already_active' }
  }
  return { canCall: true }
}
