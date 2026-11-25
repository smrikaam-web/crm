/**
 * Pure utility functions for call transcription handling and formatting.
 */

/**
 * Format an array of speech utterances into the standard CRM transcript string.
 * @param {Array<{ speaker: string, text: string }>} utterances
 * @returns {string} Formatted transcript
 */
export function formatTranscriptUtterances(utterances) {
  if (!Array.isArray(utterances) || utterances.length === 0) {
    return ''
  }

  return utterances
    .filter((u) => u && typeof u.text === 'string' && u.text.trim().length > 0)
    .map((u) => {
      const speakerLabel =
        (u.speaker || '').toLowerCase() === 'agent' ? 'Agent' : 'Customer'
      return `[${speakerLabel}]\n${u.text.trim()}`
    })
    .join('\n\n')
}

/**
 * Determine and normalize the speaker name from Twilio track data.
 * @param {string} [label] - Explicit track label (e.g., 'customer' or 'agent')
 * @param {string} [track] - 'inbound_track' or 'outbound_track'
 * @param {string} [callType] - 'Outgoing' or 'Incoming'
 * @returns {'customer' | 'agent'}
 */
export function normalizeTranscriptSpeaker(
  label = '',
  track = '',
  callType = 'Outgoing',
) {
  const normLabel = (label || '').toLowerCase().trim()
  if (['customer', 'caller', 'client', 'lead'].includes(normLabel)) {
    return 'customer'
  }
  if (['agent', 'user', 'salesperson', 'callee'].includes(normLabel)) {
    return 'agent'
  }

  // Fallback to track + callType direction
  if (track === 'inbound_track') {
    return callType === 'Outgoing' ? 'agent' : 'customer'
  }
  if (track === 'outbound_track') {
    return callType === 'Outgoing' ? 'customer' : 'agent'
  }

  return 'customer'
}

/**
 * Append or update an utterance in the live utterances list.
 * If the last utterance is from the same speaker and was partial (not final),
 * it updates in place; otherwise appends a new utterance.
 * @param {Array<Object>} utterances
 * @param {{ speaker: string, text: string, isFinal?: boolean, timestamp?: string }} newUtterance
 * @returns {Array<Object>} Updated utterances array
 */
export function appendOrUpdateUtterance(utterances, newUtterance) {
  if (!newUtterance || !newUtterance.text) return utterances

  const speaker = (newUtterance.speaker || 'customer').toLowerCase()
  const isFinal = Boolean(newUtterance.isFinal)
  const text = newUtterance.text.trim()
  const timestamp = newUtterance.timestamp || new Date().toISOString()

  const list = [...utterances]
  const lastIndex = list.length - 1

  if (
    lastIndex >= 0 &&
    list[lastIndex].speaker === speaker &&
    !list[lastIndex].isFinal
  ) {
    list[lastIndex] = {
      ...list[lastIndex],
      text,
      isFinal,
    }
  } else {
    list.push({
      speaker,
      text,
      isFinal,
      timestamp,
    })
  }

  return list
}

/**
 * Format elapsed seconds or duration string into standard mm:ss format.
 * @param {number|string} secondsOrTime
 * @returns {string} e.g. "00:08", "01:15"
 */
export function formatSpeechTimestamp(secondsOrTime) {
  if (secondsOrTime == null) return '00:00'

  if (typeof secondsOrTime === 'string') {
    const trimmed = secondsOrTime.trim()
    // If it's already hh:mm:ss, take the last mm:ss or format
    if (/^\d{2}:\d{2}:\d{2}$/.test(trimmed)) {
      const parts = trimmed.split(':')
      return `${parts[1]}:${parts[2]}`
    }
    if (/^\d{2}:\d{2}$/.test(trimmed)) {
      return trimmed
    }
    const parsed = Number(trimmed)
    if (!isNaN(parsed)) {
      return formatSpeechTimestamp(parsed)
    }
    return trimmed
  }

  const secs = Math.max(0, Math.floor(Number(secondsOrTime) || 0))
  const minutes = Math.floor(secs / 60)
  const remainingSecs = secs % 60
  return `${String(minutes).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')}`
}

/**
 * Checks whether the current browser runtime supports the Web Speech Recognition API.
 * @returns {boolean}
 */
export function hasSpeechRecognitionSupport() {
  return (
    typeof window !== 'undefined' &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
  )
}

/**
 * Formats a user-friendly display name for a transcript speaker.
 * @param {string} speaker - 'agent' or 'customer'
 * @param {string} [contactName] - Full name of the contact/prospect
 * @param {string} [agentName] - Full name of the logged-in agent
 * @returns {string} e.g. "Sam Walker (You)" or "Mohamad Farhad"
 */
export function getSpeakerDisplayName(speaker, contactName, agentName) {
  const norm = (speaker || '').toLowerCase()
  if (norm === 'agent' || norm === 'user') {
    const name = agentName || 'Agent'
    return `${name} (You)`
  }
  return contactName || 'Customer'
}

