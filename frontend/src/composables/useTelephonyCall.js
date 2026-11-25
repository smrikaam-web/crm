import { reactive, ref, computed } from 'vue'

export const activeCallState = reactive({
  status: 'idle', // 'idle' | 'initiating' | 'ringing' | 'connected' | 'disconnected' | 'failed' | 'cancelled'
  onCall: false,
  calling: false,
  phoneNumber: '',
  contact: {
    full_name: '',
    image: '',
    organization: '',
    designation: '',
    mobile_no: '',
  },
  duration: '00:00:00',
  muted: false,
  showKeypad: false,
  activeCallSid: '',
  notes: '',
  noteDocName: '',
  errorMessage: '',
  callerId: '',
  callerIdLabel: '',
  utterances: [],
  transcriptionStatus: 'idle', // 'idle' | 'listening' | 'transcribing' | 'paused' | 'error' | 'unavailable'
  transcriptionError: '',
  isMinimized: false,
  isMaximized: false,
  saveStatus: 'idle', // 'idle' | 'saving' | 'saved' | 'failed'
  lastSavedTime: '',
})

// Call handlers registered by active telephony client (TwilioCallUI)
const callHandlers = {
  makeCall: null,
  hangupCall: null,
  cancelCall: null,
  toggleMute: null,
  sendDigit: null,
  saveNote: null,
  openCallWindow: null,
  minimizeCallWindow: null,
}

export function registerTelephonyHandlers(handlers = {}) {
  Object.assign(callHandlers, handlers)
}

export function useTelephonyCall() {
  const isCallActive = computed(
    () =>
      activeCallState.onCall ||
      activeCallState.calling ||
      activeCallState.status === 'initiating' ||
      activeCallState.status === 'ringing' ||
      activeCallState.status === 'connected',
  )

  function initiateCall(number, contactData = null) {
    if (!number) return
    activeCallState.phoneNumber = number
    activeCallState.status = 'initiating'
    activeCallState.calling = true
    activeCallState.onCall = false
    activeCallState.duration = '00:00:00'
    activeCallState.muted = false
    activeCallState.showKeypad = false
    activeCallState.errorMessage = ''
    activeCallState.notes = ''
    activeCallState.noteDocName = ''

    if (contactData) {
      activeCallState.contact = {
        full_name: contactData.full_name || contactData.name || '',
        image: contactData.image || '',
        organization: contactData.organization || contactData.company || '',
        designation: contactData.designation || '',
        mobile_no: number,
      }
    }

    if (callHandlers.makeCall) {
      callHandlers.makeCall(number, contactData)
    }
  }

  function endCall() {
    if (activeCallState.onCall && callHandlers.hangupCall) {
      callHandlers.hangupCall()
    } else if (callHandlers.cancelCall) {
      callHandlers.cancelCall()
    } else if (callHandlers.hangupCall) {
      callHandlers.hangupCall()
    }
    activeCallState.calling = false
    activeCallState.onCall = false
    activeCallState.status = 'idle'
  }

  function toggleMute() {
    if (callHandlers.toggleMute) {
      callHandlers.toggleMute()
    } else {
      activeCallState.muted = !activeCallState.muted
    }
  }

  function sendDigit(digit) {
    if (callHandlers.sendDigit) {
      callHandlers.sendDigit(digit)
    }
  }

  function updateNotes(content) {
    activeCallState.notes = content
    if (callHandlers.saveNote) {
      callHandlers.saveNote(content)
    }
  }

  function setCallerId(number, label) {
    activeCallState.callerId = number
    activeCallState.callerIdLabel = label || number
  }

  function openCallWindow() {
    activeCallState.isMinimized = false
    if (callHandlers.openCallWindow) {
      callHandlers.openCallWindow()
    }
  }

  function minimizeCallWindow() {
    activeCallState.isMinimized = true
    if (callHandlers.minimizeCallWindow) {
      callHandlers.minimizeCallWindow()
    }
  }

  function toggleMaximize() {
    activeCallState.isMaximized = !activeCallState.isMaximized
  }

  function resetCallState() {
    activeCallState.status = 'idle'
    activeCallState.onCall = false
    activeCallState.calling = false
    activeCallState.phoneNumber = ''
    activeCallState.duration = '00:00:00'
    activeCallState.muted = false
    activeCallState.showKeypad = false
    activeCallState.activeCallSid = ''
    activeCallState.notes = ''
    activeCallState.noteDocName = ''
    activeCallState.errorMessage = ''
    activeCallState.utterances = []
    activeCallState.transcriptionStatus = 'idle'
    activeCallState.transcriptionError = ''
    activeCallState.saveStatus = 'idle'
    activeCallState.lastSavedTime = ''
    activeCallState.isMinimized = false
    activeCallState.isMaximized = false
  }

  return {
    state: activeCallState,
    isCallActive,
    initiateCall,
    endCall,
    toggleMute,
    sendDigit,
    updateNotes,
    setCallerId,
    openCallWindow,
    minimizeCallWindow,
    toggleMaximize,
    resetCallState,
  }
}
