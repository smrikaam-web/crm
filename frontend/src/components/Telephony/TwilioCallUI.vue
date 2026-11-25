<template>
  <div v-show="showCallPopup && !isDialPadRoute" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-72 cursor-move select-none flex-col rounded-6 bg-surface-gray-10 p-4 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="relative flex items-center justify-center [&>div]:text-[30px]"
          :class="[
            onCall || calling ? '' : 'pulse',
            onCall ? '!h-16 !w-16 [&>div]:!text-[20px]' : '!h-24 !w-24',
          ]"
        />
        <div class="flex flex-col items-center justify-center gap-1">
          <div class="text-2xl-medium">
            {{ contact?.full_name ?? __('Unknown') }}
          </div>
          <div class="text-sm text-ink-gray-5">{{ phoneNumber || contact?.mobile_no }}</div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base text-center">
            <span class="text-xs text-emerald-400 font-semibold block uppercase tracking-wider mb-0.5">
              {{ __('Connected') }}
            </span>
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base text-center">
          <span v-if="callStatus === 'initiating'">{{ __('Connecting...') }}</span>
          <span v-else-if="callStatus === 'ringing'">{{ __('Ringing...') }}</span>
          <span v-else-if="callStatus === 'connected'">{{ __('Connected') }}</span>
          <span v-else-if="callStatus === 'disconnected' || callStatus === 'completed'">{{ __('Call ended') }}</span>
          <span v-else-if="callStatus === 'cancelled'">{{ __('Call cancelled') }}</span>
          <span v-else-if="callStatus === 'failed'" class="text-surface-red-5 font-medium">
            {{ __('Call Failed') }}
          </span>
          <span v-else-if="calling">{{ __('Calling...') }}</span>
          <span v-else>{{ __('Incoming call...') }}</span>
        </div>

        <!-- Failure Details & Retry Area -->
        <div
          v-if="callStatus === 'failed'"
          class="flex flex-col items-center gap-2 px-2 text-center w-full"
        >
          <div
            v-if="callErrorMessage"
            class="text-xs text-ink-gray-4 leading-relaxed max-w-[240px] break-words"
          >
            {{ callErrorMessage }}
          </div>
          <div class="flex gap-2 mt-2">
            <Button
              size="sm"
              variant="outline"
              :label="__('Close')"
              class="rounded-6"
              @click="closeCallPopup"
            />
            <Button
              size="sm"
              variant="solid"
              theme="green"
              :label="__('Retry')"
              class="rounded-6 text-ink-base"
              :iconLeft="PhoneIcon"
              @click="retryCall"
            />
          </div>
        </div>

        <!-- Live Transcript Area -->
        <div
          v-if="onCall || utterances.length > 0"
          class="flex w-full flex-col gap-1.5 rounded-lg bg-surface-gray-9/70 p-2.5 text-left border border-surface-gray-7/50"
        >
          <div
            class="flex items-center justify-between text-[11px] font-semibold text-ink-gray-4 uppercase tracking-wider"
          >
            <div class="flex items-center gap-1.5">
              <span
                class="size-2 rounded-full"
                :class="
                  transcriptionStatus === 'error'
                    ? 'bg-amber-500'
                    : 'bg-emerald-500 animate-pulse'
                "
              />
              <span>{{ __('Live Transcript') }}</span>
            </div>
            <span
              v-if="transcriptionStatus === 'error'"
              class="text-[10px] lowercase text-ink-gray-5"
            >
              {{ __('unavailable') }}
            </span>
          </div>

          <div
            ref="transcriptContainer"
            class="flex max-h-48 min-h-[72px] w-full flex-col gap-2 overflow-y-auto pr-1 text-xs select-text scroll-smooth"
          >
            <div
              v-if="utterances.length === 0"
              class="flex h-full min-h-[60px] items-center justify-center text-center text-ink-gray-5 italic text-[11px]"
            >
              {{
                transcriptionStatus === 'error'
                  ? __('Live transcription unavailable')
                  : __('Listening for speech...')
              }}
            </div>

            <div
              v-for="(item, index) in utterances"
              :key="index"
              class="flex flex-col gap-0.5"
            >
              <div
                class="text-[11px] font-semibold"
                :class="
                  item.speaker === 'agent'
                    ? 'text-blue-400'
                    : 'text-emerald-400'
                "
              >
                {{ item.speaker === 'agent' ? __('Agent') : __('Customer') }}
              </div>
              <div
                class="rounded bg-surface-gray-8/60 px-2 py-1 text-ink-gray-2 leading-relaxed whitespace-pre-wrap break-words"
                :class="{ 'opacity-75 italic': !item.isFinal }"
              >
                {{ item.text }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="onCall" class="flex gap-2">
          <Button
            :icon="muted ? 'lucide-mic-off' : 'lucide-mic'"
            class="rounded-full"
            @click="toggleMute"
          />
          <Button
            class="cursor-pointer rounded-full"
            :class="{ 'bg-surface-gray-7': showKeypad }"
            :tooltip="__('Dialpad')"
            :icon="DialpadIcon"
            @click="toggleKeypad"
          />
          <Button
            class="cursor-pointer rounded-full"
            :class="{ 'bg-surface-gray-7 text-white ring-1 ring-white/20': showNotesPanel }"
            :tooltip="__('Call Notes')"
            :icon="NoteIcon"
            @click="toggleNotesPanel"
          />
          <Button
            class="rounded-full bg-surface-red-7 hover:bg-surface-red-8 rotate-[135deg] text-ink-base"
            :tooltip="__('Hang Up')"
            :icon="PhoneIcon"
            @click="hangUpCall"
          />
        </div>

        <!-- Dedicated In-Call Notes Area -->
        <div
          v-if="onCall && showNotesPanel"
          class="flex w-full flex-col gap-2 rounded-lg bg-surface-gray-9/90 p-2.5 text-left border border-surface-gray-7/60 shadow-inner"
        >
          <div class="flex items-center justify-between text-[11px] font-semibold text-ink-gray-3 uppercase tracking-wider">
            <div class="flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{{ __('Call Notes') }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="isSavingNote" class="text-[10px] lowercase text-amber-400 font-normal">
                {{ __('saving...') }}
              </span>
              <span v-else-if="noteSavedNotice" class="text-[10px] lowercase text-emerald-400 font-normal">
                {{ __('saved') }}
              </span>
              <button
                type="button"
                class="text-ink-gray-4 hover:text-ink-gray-2 text-xs cursor-pointer p-0.5"
                @click="showNotesPanel = false"
              >
                ✕
              </button>
            </div>
          </div>

          <textarea
            v-model="activeCallState.notes"
            rows="3"
            class="w-full resize-none rounded bg-surface-gray-8/80 p-2 text-xs text-ink-gray-2 placeholder:text-ink-gray-5 border border-surface-gray-7/50 focus:border-outline-gray-4 focus:outline-none scroll-smooth leading-relaxed"
            :placeholder="__('Type notes during call... (auto-saved)')"
            @input="handleNotesInput"
          />

          <div class="flex items-center justify-between pt-0.5">
            <span class="text-[10px] text-ink-gray-5">
              {{ __('Linked to prospect & call log') }}
            </span>
            <Button
              size="xs"
              variant="subtle"
              :label="isSavingNote ? __('Saving...') : __('Save Note')"
              :loading="isSavingNote"
              class="text-[11px] h-6 px-2.5 rounded font-medium text-ink-base bg-surface-gray-7 hover:bg-surface-gray-6"
              @click="persistCallNote(true)"
            />
          </div>
        </div>
        <div
          v-if="onCall && showKeypad"
          class="grid w-full grid-cols-3 gap-2 pt-1"
        >
          <Button
            v-for="digit in keypadDigits"
            :key="digit"
            variant="subtle"
            class="!h-9 justify-center text-base font-medium"
            :label="digit"
            @click="sendDigit(digit)"
          />
        </div>
        <div v-else-if="calling || callStatus == 'initiating' || callStatus == 'ringing'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            class="rounded-6 text-ink-base"
            @click="cancelCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else-if="callStatus === 'failed' || callStatus === 'disconnected' || callStatus === 'cancelled'">
          <!-- Handled above with retry/close buttons or status message -->
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="__('Accept')"
            class="rounded-6 text-ink-base"
            :iconLeft="PhoneIcon"
            @click="acceptIncomingCall"
          />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Reject')"
            class="rounded-6 text-ink-base"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <div
    v-show="showSmallCallWindow && !isDialPadRoute"
    class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-6 bg-surface-gray-10 px-2 py-[7px] text-base text-ink-gray-2"
    v-bind="$attrs"
    @click="toggleCallWindow"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate">
        {{ contact?.full_name ?? __('Unknown') }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :icon="PhoneIcon"
        @click.stop="hangUpCall"
      />
    </div>
    <div
      v-else-if="calling || callStatus == 'initiating' || callStatus == 'ringing'"
      class="flex items-center gap-3"
    >
      <div class="my-1">
        {{ callStatus == 'ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :icon="PhoneIcon"
        @click.stop="cancelCall"
      />
    </div>
    <div v-else-if="callStatus === 'failed'" class="flex items-center gap-2">
      <span class="text-xs text-surface-red-5 font-medium">{{ __('Call Failed') }}</span>
      <Button
        variant="outline"
        size="sm"
        class="!h-6 text-xs"
        :label="__('Close')"
        @click.stop="closeCallPopup"
      />
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full animate-pulse text-ink-base"
        :tooltip="__('Accept Call')"
        :icon="PhoneIcon"
        @click.stop="acceptIncomingCall"
      />
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :tooltip="__('Reject Call')"
        :icon="PhoneIcon"
        @click.stop="rejectIncomingCall"
      />
    </div>
  </div>
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { Device } from '@twilio/voice-sdk'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { globalStore } from '@/stores/global'
import {
  formatTranscriptUtterances,
  appendOrUpdateUtterance,
} from '@/utils/callTranscript'
import {
  validateTokenResponse,
  mapTwilioSignalingStatus,
  extractCallErrorMessage,
} from '@/utils/twilioCall'
import { Avatar, call, createResource, toast } from 'frappe-ui'
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { activeCallState, registerTelephonyHandlers } from '@/composables/useTelephonyCall'

const route = useRoute()
const isDialPadRoute = computed(() => {
  const name = route?.name
  const path = route?.path || ''
  return (
    name === 'DialPad' ||
    path === '/calling/dialpad' ||
    path === '/dialpad' ||
    path.startsWith('/calling/dialpad') ||
    path.startsWith('/dialpad')
  )
})

const { capture } = useTelemetry()
const { $socket } = globalStore()

let device = null
let log = ref('Connecting...')
let _call = null

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let muted = ref(false)
let showKeypad = ref(false)
let callPopup = ref(null)
let counterUp = ref(null)
let callStatus = ref('')

const deviceStatus = ref('uninitialized') // 'uninitialized', 'initializing', 'registering', 'ready', 'error'
const deviceErrorMessage = ref('')
const callErrorMessage = ref('')
let isCallPendingConnect = false
let closeStatusTimer = null

const activeCallSid = ref('')
const utterances = ref([])
const transcriptionStatus = ref('idle')
const transcriptContainer = ref(null)
let transcriptSaved = false

const keypadDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

const phoneNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

const showNotesPanel = ref(false)
const isSavingNote = ref(false)
const noteSavedNotice = ref(false)
let notesDebounceTimer = null

function toggleNotesPanel() {
  showNotesPanel.value = !showNotesPanel.value
}

function handleNotesInput() {
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  notesDebounceTimer = setTimeout(() => {
    persistCallNote(false)
  }, 1200)
}

async function persistCallNote(isExplicit = false) {
  const content = (activeCallState.notes || '').trim()
  const sid = activeCallSid.value || _call?.parameters?.CallSid || activeCallState.activeCallSid
  if (!content && !activeCallState.noteDocName) {
    return
  }
  if (!sid) {
    return
  }

  isSavingNote.value = true
  try {
    const res = await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: sid,
      note: {
        name: activeCallState.noteDocName || undefined,
        title: __('Call Note') + (contact.value?.full_name ? ` - ${contact.value.full_name}` : ''),
        content: activeCallState.notes,
      },
    })
    if (res?.name) {
      activeCallState.noteDocName = res.name
    }
    noteSavedNotice.value = true
    setTimeout(() => {
      noteSavedNotice.value = false
    }, 2500)
    if (isExplicit) {
      toast.success(__('Call note saved'))
    }
    capture('note_updated')
  } catch (err) {
    console.error('Failed to save in-call note:', err)
    if (isExplicit) {
      toast.error(__('Failed to save note'))
    }
  } finally {
    isSavingNote.value = false
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 320, y: height.value - 380 },
  preventDefault: true,
})

function handleLiveTranscriptEvent(data) {
  if (!data || !data.text) return

  // Filter out if not for this call
  if (activeCallSid.value && data.call_sid && data.call_sid !== activeCallSid.value) {
    return
  }
  if (!activeCallSid.value && data.call_sid) {
    activeCallSid.value = data.call_sid
  }

  transcriptionStatus.value = 'listening'

  utterances.value = appendOrUpdateUtterance(utterances.value, {
    speaker: data.speaker,
    text: data.text,
    isFinal: data.is_final,
    timestamp: data.timestamp,
  })

  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (transcriptContainer.value) {
      transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
    }
  })
}

async function saveFinalTranscript() {
  if (transcriptSaved) return
  const sid = activeCallSid.value || _call?.parameters?.CallSid
  if (!sid || utterances.value.length === 0) return

  transcriptSaved = true
  const formatted = formatTranscriptUtterances(utterances.value)

  try {
    await call('crm.integrations.twilio.api.save_call_transcript', {
      call_sid: sid,
      transcript: formatted,
    })
  } catch (err) {
    console.error('Failed to save call transcript to CRM:', err)
  }
}

function resetTranscriptState() {
  utterances.value = []
  activeCallSid.value = ''
  transcriptionStatus.value = 'idle'
  transcriptSaved = false
}

function handleSocketMessage(data) {
  if (!data) return
  if (data.event === 'started') {
    transcriptionStatus.value = 'listening'
    return
  }
  if (data.event === 'stopped') {
    return
  }
  if (data.event === 'content') {
    handleLiveTranscriptEvent(data)
  }
}

function setupSocket() {
  if ($socket) {
    $socket.on('twilio_transcription', handleSocketMessage)
  }
}

onMounted(() => {
  setupSocket()
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('twilio_transcription', handleSocketMessage)
  }
})

async function startupClient() {
  if (deviceStatus.value === 'initializing' || deviceStatus.value === 'registering') {
    return false
  }

  deviceStatus.value = 'initializing'
  deviceErrorMessage.value = ''
  log.value = 'Requesting Access Token...'

  try {
    setupSocket()
    const data = await call('crm.integrations.twilio.api.generate_access_token')

    const validation = validateTokenResponse(data)
    if (!validation.ok) {
      const msg = __(validation.message)
      deviceStatus.value = 'error'
      deviceErrorMessage.value = msg
      log.value = msg
      return false
    }

    log.value = 'Got a token.'
    intitializeDevice(validation.token)
    return true
  } catch (err) {
    const msg =
      err.messages?.[0] ||
      err.message ||
      __('An error occurred while requesting Twilio access token.')
    deviceStatus.value = 'error'
    deviceErrorMessage.value = msg
    log.value = msg
    return false
  }
}

function intitializeDevice(token) {
  if (!token) {
    deviceStatus.value = 'error'
    deviceErrorMessage.value = __('Invalid Twilio token received.')
    log.value = deviceErrorMessage.value
    return
  }

  try {
    if (device && typeof device.destroy === 'function') {
      try {
        device.destroy()
      } catch (e) {
        console.warn('Error destroying existing device instance:', e)
      }
    }

    device = new Device(token, {
      codecPreferences: ['opus', 'pcmu'],
      fakeLocalDTMF: true,
      enableRingingState: true,
    })

    addDeviceListeners()
    deviceStatus.value = 'registering'
    device.register()
  } catch (err) {
    deviceStatus.value = 'error'
    deviceErrorMessage.value =
      err.message || __('Failed to initialize Twilio device.')
    log.value = deviceErrorMessage.value
  }
}

function addDeviceListeners() {
  if (!device) return

  device.on('registered', () => {
    deviceStatus.value = 'ready'
    deviceErrorMessage.value = ''
    log.value = 'Ready to make and receive calls!'
  })

  device.on('registering', () => {
    deviceStatus.value = 'registering'
    log.value = 'Registering Twilio device...'
  })

  device.on('unregistered', () => {
    deviceStatus.value = 'unregistered'
    log.value = 'Twilio device unregistered'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + (error.message || error)
    let userMsg = error.message || __('Twilio connection error')
    if (error.code === 31204 || error.code === 31205) {
      userMsg = __('Twilio authentication expired. Please refresh.')
    }
    deviceErrorMessage.value = userMsg

    if (calling.value && !onCall.value) {
      callStatus.value = 'failed'
      calling.value = false
      callErrorMessage.value = userMsg
    }
    if (!onCall.value && !calling.value) {
      deviceStatus.value = 'error'
    }
  })

  device.on('incoming', handleIncomingCall)

  device.on('tokenWillExpire', async () => {
    try {
      const data = await call('crm.integrations.twilio.api.generate_access_token')
      if (data?.token && device) {
        device.updateToken(data.token)
      }
    } catch (e) {
      console.error('Failed to refresh Twilio token:', e)
    }
  })
}

function waitForDeviceRegistered(timeoutMs = 6000) {
  return new Promise((resolve) => {
    if (device?.state === 'registered' || deviceStatus.value === 'ready') {
      return resolve(true)
    }

    let timer = null
    const onRegistered = () => {
      cleanup()
      resolve(true)
    }
    const onError = () => {
      cleanup()
      resolve(false)
    }
    const cleanup = () => {
      if (timer) clearTimeout(timer)
      device?.removeListener('registered', onRegistered)
      device?.removeListener('error', onError)
    }

    timer = setTimeout(() => {
      cleanup()
      resolve(device?.state === 'registered' || deviceStatus.value === 'ready')
    }, timeoutMs)

    device?.once('registered', onRegistered)
    device?.once('error', onError)
  })
}

function toggleMute() {
  if (!_call) return
  if (_call.isMuted()) {
    _call.mute(false)
    muted.value = false
  } else {
    _call.mute()
    muted.value = true
  }
}

function toggleKeypad() {
  showKeypad.value = !showKeypad.value
}

function sendDigit(digit) {
  if (_call && onCall.value) {
    _call.sendDigits(digit)
  }
}

function handleIncomingCall(call) {
  resetTranscriptState()
  log.value = `Incoming call from ${call.parameters.From}`
  phoneNumber.value = call.parameters.From

  showCallPopup.value = true
  _call = call
  if (call.parameters?.CallSid) {
    activeCallSid.value = call.parameters.CallSid
  }

  _call.on('accept', (conn) => {
    console.log('conn', conn)
    if (_call?.parameters?.CallSid) {
      activeCallSid.value = _call.parameters.CallSid
    }
  })

  // add event listener to call object
  call.on('cancel', handleDisconnectedIncomingCall)
  call.on('disconnect', handleDisconnectedIncomingCall)
  call.on('reject', handleDisconnectedIncomingCall)
}

async function acceptIncomingCall() {
  log.value = 'Accepted incoming call.'
  onCall.value = true
  callStatus.value = 'connected'
  if (_call?.parameters?.CallSid) {
    activeCallSid.value = _call.parameters.CallSid
  }
  await _call.accept()
  counterUp.value?.start()
}

function rejectIncomingCall() {
  if (_call) {
    try {
      _call.reject()
    } catch (e) {}
  }
  log.value = 'Rejected incoming call'
  closeCallPopup()
}

async function hangUpCall() {
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  log.value = 'Hanging up call'
  if (_call) {
    try {
      _call.disconnect()
    } catch (e) {
      console.warn('Error disconnecting on hangup:', e)
    }
  }
  handleCallDisconnected()
}

async function handleDisconnectedIncomingCall() {
  log.value = `Call ended from handle disconnected Incoming call.`
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  closeCallPopup()
}

async function makeOutgoingCall(number) {
  if (!number) {
    toast.error(__('Please enter a valid phone number to call.'))
    return
  }

  // Prevent multiple simultaneous outgoing call attempts
  if (onCall.value || calling.value || callStatus.value === 'initiating' || isCallPendingConnect) {
    toast.warning(__('A call is already in progress.'))
    return
  }

  if (closeStatusTimer) {
    clearTimeout(closeStatusTimer)
    closeStatusTimer = null
  }

  isCallPendingConnect = true
  phoneNumber.value = number
  resetTranscriptState()

  // Immediately display calling popup to give user feedback & control
  showCallPopup.value = true
  showSmallCallWindow.value = false
  callStatus.value = 'initiating'
  calling.value = true
  onCall.value = false
  muted.value = false
  showKeypad.value = false
  callErrorMessage.value = ''

  try {
    // 1. Ensure Device is ready
    if (!device || deviceStatus.value !== 'ready') {
      log.value = 'Twilio device not ready. Initializing...'
      const ok = await startupClient()
      if (!ok || !device) {
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value =
          deviceErrorMessage.value ||
          __(
            'Twilio telephony service is not ready. Please verify your phone mapping and settings.',
          )
        return
      }

      if (device.state !== 'registered') {
        await waitForDeviceRegistered(6000)
      }

      if (deviceStatus.value === 'error') {
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value =
          deviceErrorMessage.value || __('Twilio registration failed.')
        return
      }
    }

    // Check if user cancelled while device was preparing
    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      return
    }

    // 2. Microphone permission validation
    if (navigator?.mediaDevices?.getUserMedia) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true })
      } catch (micErr) {
        console.warn('Microphone permission check failed:', micErr)
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value = __(
          'Microphone permission denied. Please allow microphone access in your browser to place calls.',
        )
        return
      }
    }

    // Check if user cancelled while microphone prompt was active
    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      return
    }

    // 3. Initiate Twilio connection
    log.value = `Attempting to call ${number} ...`
    callStatus.value = 'initiating'

    const callParams = { To: number }
    if (activeCallState.callerId) {
      callParams.callerId = activeCallState.callerId
      callParams.From = activeCallState.callerId
    }

    _call = await device.connect({
      params: callParams,
    })

    if (_call?.parameters?.CallSid) {
      activeCallSid.value = _call.parameters.CallSid
    }

    // Check if user cancelled while connect was awaiting
    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      if (_call) {
        try {
          _call.disconnect()
        } catch (e) {}
        _call = null
      }
      return
    }

    capture('make_outgoing_call')
    attachOutgoingCallListeners(_call)
  } catch (error) {
    console.error('Error during makeOutgoingCall:', error)
    log.value = `Could not connect call: ${error.message}`
    callStatus.value = 'failed'
    calling.value = false
    transcriptionStatus.value = 'error'
    callErrorMessage.value = __(extractCallErrorMessage(error))
  } finally {
    isCallPendingConnect = false
  }
}

function attachOutgoingCallListeners(callInstance) {
  if (!callInstance) return

  // Ringing event from Voice SDK (when enableRingingState: true)
  callInstance.on('ringing', () => {
    log.value = 'Ringing...'
    if (!onCall.value) {
      callStatus.value = 'ringing'
      activeCallState.status = 'ringing'
    }
  })

  // Status message received from TwiML callback
  callInstance.on('messageReceived', (message) => {
    let info = message?.content
    if (typeof info === 'string') {
      try {
        info = JSON.parse(info)
      } catch (e) {
        // use raw string
      }
    }
    if (!info) return

    const rawStatus = info.CallStatus || info.call_status || info.status
    const signalingStatus = mapTwilioSignalingStatus(rawStatus)
    if (info.ParentCallSid) {
      activeCallSid.value = info.ParentCallSid
    } else if (info.CallSid && !activeCallSid.value) {
      activeCallSid.value = info.CallSid
    }

    log.value = `Call status update: ${rawStatus}`

    if (signalingStatus === 'ringing') {
      if (!onCall.value) {
        callStatus.value = 'ringing'
      }
    } else if (signalingStatus === 'connected') {
      log.value = 'Call in progress (answered).'
      callStatus.value = 'connected'
      calling.value = false
      onCall.value = true
      counterUp.value?.start()
    } else if (
      signalingStatus === 'busy' ||
      signalingStatus === 'no-answer' ||
      signalingStatus === 'failed'
    ) {
      log.value = `Call not completed: ${rawStatus}`
      callStatus.value = 'failed'
      calling.value = false
      onCall.value = false
      counterUp.value?.stop()
      callErrorMessage.value =
        signalingStatus === 'busy'
          ? __('Line is busy.')
          : signalingStatus === 'no-answer'
            ? __('No answer from recipient.')
            : __('Call failed to connect.')
    } else if (signalingStatus === 'completed') {
      handleCallDisconnected()
    }
  })

  callInstance.on('accept', () => {
    log.value = 'Call stream accepted by Twilio'
    if (callInstance?.parameters?.CallSid) {
      activeCallSid.value = callInstance.parameters.CallSid
    }
    onCall.value = true
    calling.value = false
    callStatus.value = 'connected'
    activeCallState.onCall = true
    activeCallState.calling = false
    activeCallState.status = 'connected'
    counterUp.value?.start()
  })

  callInstance.on('disconnect', () => {
    handleCallDisconnected()
  })

  callInstance.on('cancel', () => {
    log.value = 'Call cancelled'
    handleCallCancelled()
  })

  callInstance.on('error', (err) => {
    console.error('Twilio Call Error:', err)
    log.value = 'Call error: ' + (err.message || err)
    callStatus.value = 'failed'
    calling.value = false
    onCall.value = false
    callErrorMessage.value = err.message || __('Call encountered an error.')
    counterUp.value?.stop()
  })
}

async function handleCallDisconnected() {
  log.value = 'Call ended (disconnected).'
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  callStatus.value = 'disconnected'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'disconnected'
  activeCallState.calling = false
  activeCallState.onCall = false
  counterUp.value?.stop()
  muted.value = false
  showKeypad.value = false

  if (closeStatusTimer) clearTimeout(closeStatusTimer)
  closeStatusTimer = setTimeout(() => {
    if (callStatus.value === 'disconnected') {
      closeCallPopup()
    }
  }, 2000)
}

function handleCallCancelled() {
  callStatus.value = 'cancelled'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'cancelled'
  activeCallState.calling = false
  activeCallState.onCall = false
  counterUp.value?.stop()
  muted.value = false
  showKeypad.value = false

  if (closeStatusTimer) clearTimeout(closeStatusTimer)
  closeStatusTimer = setTimeout(() => {
    if (callStatus.value === 'cancelled') {
      closeCallPopup()
    }
  }, 1200)
}

function cancelCall() {
  log.value = 'User clicked Cancel.'
  callStatus.value = 'cancelled'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'cancelled'
  activeCallState.calling = false
  activeCallState.onCall = false

  if (_call) {
    try {
      _call.disconnect()
    } catch (e) {
      console.warn('Error disconnecting call on cancel:', e)
    }
    _call = null
  }

  counterUp.value?.stop()
  resetTranscriptState()
  closeCallPopup()
}

function retryCall() {
  callStatus.value = ''
  callErrorMessage.value = ''
  if (phoneNumber.value) {
    makeOutgoingCall(phoneNumber.value)
  }
}

function closeCallPopup() {
  if (closeStatusTimer) {
    clearTimeout(closeStatusTimer)
    closeStatusTimer = null
  }
  showCallPopup.value = false
  showSmallCallWindow.value = false
  showKeypad.value = false
  showNotesPanel.value = false
  isSavingNote.value = false
  noteSavedNotice.value = false
  if (notesDebounceTimer) {
    clearTimeout(notesDebounceTimer)
    notesDebounceTimer = null
  }
  callStatus.value = ''
  callErrorMessage.value = ''
  calling.value = false
  onCall.value = false
  muted.value = false
  activeCallState.status = 'idle'
  activeCallState.onCall = false
  activeCallState.calling = false
  activeCallState.duration = '00:00:00'
  _call = null
  resetTranscriptState()
}

function isCallInProgress() {
  return Boolean(
    onCall.value ||
    calling.value ||
    callStatus.value === 'initiating' ||
    callStatus.value === 'ringing' ||
    isCallPendingConnect,
  )
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
}

watch(onCall, (value) => {
  if (!value) {
    showKeypad.value = false
  }
})

watch(
  () => log.value,
  (value) => {
    console.log(value)
  },
  { immediate: true },
)

// Sync internal telephony state to shared activeCallState
watch(callStatus, (val) => {
  activeCallState.status = val || (onCall.value ? 'connected' : calling.value ? 'initiating' : 'idle')
})
watch(onCall, (val) => {
  activeCallState.onCall = val
  if (!val) {
    activeCallState.duration = '00:00:00'
  }
})
watch(calling, (val) => {
  activeCallState.calling = val
})
watch(phoneNumber, (val) => {
  activeCallState.phoneNumber = val || ''
})
watch(
  contact,
  (val) => {
    if (val) {
      activeCallState.contact = {
        full_name: val.full_name || activeCallState.contact.full_name || '',
        image: val.image || activeCallState.contact.image || '',
        mobile_no: val.mobile_no || activeCallState.contact.mobile_no || '',
        organization: val.company_name || val.organization || activeCallState.contact.organization || '',
        designation: val.designation || activeCallState.contact.designation || '',
      }
    }
  },
  { deep: true },
)
watch(muted, (val) => {
  activeCallState.muted = val
})
watch(activeCallSid, (val) => {
  activeCallState.activeCallSid = val
})
watch(callErrorMessage, (val) => {
  activeCallState.errorMessage = val
})

let durationSyncTimer = null
onMounted(() => {
  durationSyncTimer = setInterval(() => {
    if (onCall.value && counterUp.value?.updatedTime) {
      activeCallState.duration = counterUp.value.updatedTime
    }
  }, 500)

  registerTelephonyHandlers({
    makeCall: (num, contactData) => {
      if (contactData) {
        activeCallState.contact = {
          full_name: contactData.full_name || contactData.name || '',
          image: contactData.image || '',
          organization: contactData.organization || contactData.company || '',
          designation: contactData.designation || '',
          mobile_no: num,
        }
      }
      makeOutgoingCall(num)
    },
    hangupCall: () => hangUpCall(),
    cancelCall: () => cancelCall(),
    toggleMute: () => toggleMute(),
    sendDigit: (d) => sendDigit(d),
    saveNote: (content) => {
      activeCallState.notes = content
      handleNotesInput()
    },
  })
})

onBeforeUnmount(() => {
  if (durationSyncTimer) {
    clearInterval(durationSyncTimer)
  }
})

defineExpose({
  makeOutgoingCall,
  setup: startupClient,
  isCallInProgress,
  closeCallPopup,
})
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
