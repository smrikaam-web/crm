<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Breadcrumbs and Header -->
    <header class="border-b border-outline-gray-2 px-6 py-4 dark:border-outline-gray-7">
      <!-- Breadcrumb navigation -->
      <div class="mb-2 flex items-center gap-1.5 text-xs text-ink-gray-5">
        <router-link to="/dashboard" class="flex items-center hover:text-ink-gray-8 dark:hover:text-ink-gray-3">
          <LucideHome class="size-3.5 text-ink-gray-4" />
        </router-link>
        <span>&gt;</span>
        <span>{{ __('Calling') }}</span>
        <span>/</span>
        <span class="font-medium text-ink-gray-9 dark:text-ink-white">{{ __('Dial Pad') }}</span>
      </div>

      <!-- Main Header Row -->
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-bold tracking-tight text-ink-gray-9 dark:text-ink-white">
              {{ __('Dial Pad') }}
            </h1>
            <span class="text-ink-gray-4">•</span>
            <span class="text-sm font-medium text-ink-gray-6 dark:text-ink-gray-4">
              {{ __('power dialer') }}
            </span>
          </div>
          <p class="mt-0.5 text-xs text-ink-gray-5">
            {{ __('One queue, zero busywork. AI dials, logs, transcribes and coaches — you just talk.') }}
          </p>
        </div>

        <!-- Top Right: From / Caller ID Dropdown -->
        <div class="relative">
          <Dropdown :options="callerIdDropdownOptions">
            <button
              type="button"
              class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-base px-3 py-1.5 text-xs font-medium text-ink-gray-8 shadow-xs hover:bg-surface-gray-2 dark:border-outline-gray-7 dark:text-ink-gray-2 dark:hover:bg-surface-gray-8"
            >
              <span class="text-ink-gray-5">{{ __('From:') }}</span>
              <span class="font-semibold text-ink-gray-9 dark:text-ink-white">
                {{ selectedCallerId.label }}
              </span>
              <span class="lucide-chevron-down size-3.5 text-ink-gray-5" />
            </button>
          </Dropdown>
        </div>
      </div>
    </header>

    <!-- Main 3-Column Layout -->
    <div class="flex-1 p-6">
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        
        <!-- ========================================== -->
        <!-- COLUMN 1: LEFT (Keypad & My Task Numbers) -->
        <!-- ========================================== -->
        <div class="flex flex-col gap-5 lg:col-span-4">
          <!-- Keypad Card -->
          <div class="rounded-2xl border border-outline-gray-2 bg-surface-white p-5 shadow-xs dark:border-outline-gray-7 dark:bg-surface-gray-8">
            <!-- Number Input & Country Code -->
            <div class="mb-4">
              <div class="flex items-center gap-2 rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-1.5 dark:border-outline-gray-7 dark:bg-surface-gray-9">
                <!-- Country Code Selector Dropdown -->
                <Dropdown :options="countryCodeOptions">
                  <button
                    type="button"
                    class="flex items-center gap-1 rounded-lg bg-surface-white px-2 py-1.5 text-xs font-semibold text-ink-gray-8 shadow-2xs hover:bg-surface-gray-2 dark:bg-surface-gray-8 dark:text-ink-gray-2"
                  >
                    <span>{{ selectedCountry.code }}</span>
                    <span>{{ selectedCountry.iso }}</span>
                    <span class="lucide-chevron-down size-3 text-ink-gray-5" />
                  </button>
                </Dropdown>

                <!-- Phone input -->
                <input
                  v-model="inputNumber"
                  type="tel"
                  :placeholder="__('Enter number')"
                  class="flex-1 bg-transparent px-2 text-sm font-semibold text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none dark:text-ink-white"
                  @keydown.enter.prevent="handleCallButton"
                />

                <!-- Backspace button -->
                <button
                  v-if="inputNumber"
                  type="button"
                  class="p-1.5 text-ink-gray-4 hover:text-ink-gray-7 dark:hover:text-ink-gray-2"
                  @click="backspaceDigit"
                >
                  <LucideDelete class="size-4" />
                </button>
              </div>

              <!-- Prefix Hint -->
              <p class="mt-1.5 px-1 text-[11px] text-ink-gray-4">
                {{ __('Prefix {0} will be added - Enter to call', [selectedCountry.code]) }}
              </p>
            </div>

            <!-- 3x4 Dialpad Grid -->
            <div class="grid grid-cols-3 gap-2.5">
              <button
                v-for="k in keypadKeys"
                :key="k.digit"
                type="button"
                class="flex h-13 flex-col items-center justify-center rounded-xl border border-outline-gray-1 bg-surface-gray-1 transition-all hover:bg-surface-gray-2 active:scale-95 dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:hover:bg-surface-gray-8"
                @click="pressKeypad(k.digit)"
              >
                <span class="text-base font-bold text-ink-gray-9 dark:text-ink-white">
                  {{ k.digit }}
                </span>
                <span v-if="k.letters" class="text-[9px] font-medium tracking-wider text-ink-gray-4">
                  {{ k.letters }}
                </span>
              </button>
            </div>

            <!-- Call Action Button & Status -->
            <div class="mt-5 flex flex-col items-center justify-center gap-2">
              <button
                type="button"
                class="flex size-14 items-center justify-center rounded-full bg-[#22c55e] text-white shadow-lg transition-transform hover:bg-[#16a34a] active:scale-95 disabled:opacity-50"
                :disabled="isCallActive"
                @click="handleCallButton($event)"
              >
                <PhoneIcon class="size-6 text-white" />
              </button>
              <div class="flex items-center gap-1.5 text-xs font-medium text-ink-gray-6 dark:text-ink-gray-4">
                <span
                  class="size-2 rounded-full"
                  :class="isCallActive ? 'bg-emerald-500 animate-pulse' : 'bg-emerald-500'"
                />
                <span>{{ isCallActive ? __('On Call') : __('Ready') }}</span>
              </div>
            </div>
          </div>

          <!-- My Task Numbers Section -->
          <div class="rounded-2xl border border-outline-gray-2 bg-surface-white p-4 shadow-xs dark:border-outline-gray-7 dark:bg-surface-gray-8">
            <!-- Header -->
            <div class="mb-3 flex items-center justify-between border-b border-outline-gray-2 pb-2.5 dark:border-outline-gray-7">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-bold text-ink-gray-9 dark:text-ink-white">
                  {{ __('My Task Numbers') }}
                </span>
                <span class="text-ink-gray-4">•</span>
                <Badge variant="subtle" size="sm" class="font-bold">
                  {{ filteredTaskNumbers.length }}
                </Badge>
              </div>

              <!-- Filter Dropdown -->
              <Dropdown :options="taskFilterOptions">
                <button
                  type="button"
                  class="flex items-center gap-1 text-xs font-semibold text-ink-gray-6 hover:text-ink-gray-9 dark:text-ink-gray-4 dark:hover:text-ink-white"
                >
                  <span>{{ currentTaskFilterLabel }}</span>
                  <span class="lucide-chevron-down size-3" />
                </button>
              </Dropdown>
            </div>

            <!-- Prospect Numbers List -->
            <div class="max-h-84 space-y-2 overflow-y-auto pr-1">
              <div
                v-if="loadingTasks"
                class="py-6 text-center text-xs text-ink-gray-4"
              >
                {{ __('Loading assigned prospects...') }}
              </div>

              <div
                v-else-if="filteredTaskNumbers.length === 0"
                class="py-8 text-center text-xs text-ink-gray-4"
              >
                {{ __('No assigned task numbers found.') }}
              </div>

              <div
                v-for="item in filteredTaskNumbers"
                :key="item.name"
                class="group flex items-center justify-between gap-3 rounded-xl border border-outline-gray-1 bg-surface-gray-1 p-2.5 transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-2 dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:hover:bg-surface-gray-8"
              >
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                  <!-- Colored Avatar Initials -->
                  <div
                    class="flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow-xs"
                    :style="{ backgroundColor: getAvatarColor(item.contact_name) }"
                  >
                    {{ getInitials(item.contact_name) }}
                  </div>

                  <!-- Details -->
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-xs font-semibold text-ink-gray-9 dark:text-ink-white">
                      {{ item.contact_name }}
                    </p>
                    <p class="truncate text-[11px] text-ink-gray-5">
                      {{ item.organization || item.designation || __('Prospect') }}
                    </p>
                  </div>
                </div>

                <!-- Phone number & Call Icon -->
                <div class="flex items-center gap-2 shrink-0">
                  <span class="font-mono text-xs text-ink-gray-7 dark:text-ink-gray-3">
                    {{ item.mobile_no || item.phone }}
                  </span>
                  <button
                    type="button"
                    class="flex size-7 items-center justify-center rounded-full bg-surface-white text-ink-gray-6 shadow-2xs transition hover:bg-emerald-50 hover:text-emerald-600 dark:bg-surface-gray-8 dark:text-ink-gray-3 dark:hover:bg-emerald-950/40 dark:hover:text-emerald-400"
                    :tooltip="__('Call now')"
                    @click="dialProspect(item, $event)"
                  >
                    <PhoneIcon class="size-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- COLUMN 2: CENTER (Ready to Call / Active Call) -->
        <!-- ========================================== -->
        <div class="flex min-h-[500px] flex-col items-center justify-center rounded-2xl border border-outline-gray-2 bg-surface-gray-1 p-6 dark:border-outline-gray-7 dark:bg-surface-gray-8/50 lg:col-span-5">
          <!-- 1. Idle State: Ready to call -->
          <div
            v-if="!isCallActive"
            class="flex flex-col items-center justify-center text-center py-16"
          >
            <div class="mb-4 flex size-20 items-center justify-center rounded-full border-2 border-dashed border-outline-gray-3 text-ink-gray-4 dark:border-outline-gray-6">
              <PhoneIcon class="size-8 text-ink-gray-4" />
            </div>
            <h3 class="text-base font-bold text-ink-gray-9 dark:text-ink-white">
              {{ __('Ready to call') }}
            </h3>
            <p class="mt-1 text-xs text-ink-gray-5">
              {{ __('Enter a number and press the green button') }}
            </p>
          </div>

          <!-- 2. Active Call State: Dark Floating Card (Matches Reference Image Exactly) -->
          <div
            v-else
            class="relative flex w-full max-w-[340px] flex-col items-center rounded-3xl bg-[#172133] p-6 text-white shadow-2xl border border-slate-700/60"
          >
            <!-- Top Status Bar: Status, Timer, Signal -->
            <div class="mb-4 flex w-full items-center justify-between text-xs">
              <div class="flex items-center gap-1.5 font-medium">
                <span class="size-2 rounded-full bg-emerald-400 animate-pulse" />
                <span class="text-slate-200">
                  {{ state.status === 'initiating' ? __('Connecting...') : state.status === 'ringing' ? __('Ringing...') : __('On Call') }}
                </span>
                <span class="text-slate-400 ml-1 font-mono text-[11px]">
                  {{ state.duration || '00:00:00' }}
                </span>
              </div>

              <!-- Signal Strength Bars -->
              <div class="flex items-end gap-0.5">
                <span class="h-1.5 w-0.5 rounded-full bg-emerald-400" />
                <span class="h-2.5 w-0.5 rounded-full bg-emerald-400" />
                <span class="h-3.5 w-0.5 rounded-full bg-emerald-400" />
                <span class="h-4.5 w-0.5 rounded-full bg-emerald-400" />
              </div>
            </div>

            <!-- Large Circular Initials Avatar -->
            <div
              class="my-3 flex size-20 items-center justify-center rounded-full text-2xl font-bold shadow-md"
              :style="{ backgroundColor: getAvatarColor(activeProspectName) }"
            >
              {{ getInitials(activeProspectName) }}
            </div>

            <!-- Phone Number -->
            <div class="mt-2 text-xl font-bold tracking-wide text-white">
              {{ state.phoneNumber || __('Unknown') }}
            </div>

            <!-- Contact Name with Phone Icon -->
            <div class="mt-1 flex items-center gap-1 text-xs text-slate-300">
              <PhoneIcon class="size-3 text-slate-400" />
              <span>{{ activeProspectName }}</span>
            </div>

            <!-- Company Name -->
            <div class="mt-0.5 text-xs text-slate-400">
              {{ state.contact?.organization || activeProspectCompany || __('Prospect') }}
            </div>

            <!-- Control Buttons: Mute, Keypad, Notes -->
            <div class="my-6 flex items-center justify-center gap-6">
              <!-- Mute -->
              <div class="flex flex-col items-center gap-1.5">
                <button
                  type="button"
                  class="flex size-11 items-center justify-center rounded-full transition-colors"
                  :class="state.muted ? 'bg-red-600 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'"
                  @click="toggleMute"
                >
                  <LucideMicOff v-if="state.muted" class="size-5" />
                  <LucideMic v-else class="size-5" />
                </button>
                <span class="text-[11px] text-slate-400">{{ __('Mute') }}</span>
              </div>

              <!-- In-call Keypad -->
              <div class="flex flex-col items-center gap-1.5">
                <button
                  type="button"
                  class="flex size-11 items-center justify-center rounded-full transition-colors"
                  :class="showInCallKeypad ? 'bg-slate-500 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'"
                  @click="showInCallKeypad = !showInCallKeypad"
                >
                  <DialpadIcon class="size-5" />
                </button>
                <span class="text-[11px] text-slate-400">{{ __('Keypad') }}</span>
              </div>

              <!-- Notes Toggle -->
              <div class="flex flex-col items-center gap-1.5">
                <button
                  type="button"
                  class="flex size-11 items-center justify-center rounded-full bg-slate-700/80 text-slate-200 hover:bg-slate-600"
                  @click="focusNotesTextarea"
                >
                  <LucideFileText class="size-5" />
                </button>
                <span class="text-[11px] text-slate-400">{{ __('Notes') }}</span>
              </div>
            </div>

            <!-- In-call DTMF Keypad (Collapsible) -->
            <div
              v-if="showInCallKeypad"
              class="mb-4 grid w-full grid-cols-3 gap-1.5 rounded-xl bg-slate-800/80 p-2"
            >
              <button
                v-for="digit in dtmfDigits"
                :key="digit"
                type="button"
                class="h-8 rounded bg-slate-700/50 text-xs font-semibold text-white hover:bg-slate-600"
                @click="sendDigit(digit)"
              >
                {{ digit }}
              </button>
            </div>

            <!-- Decline / Hang Up Button -->
            <div class="flex flex-col items-center gap-1">
              <button
                type="button"
                class="flex size-14 items-center justify-center rounded-full bg-[#ef4444] text-white shadow-lg transition-transform hover:bg-[#dc2626] active:scale-95"
                @click="endCall"
              >
                <PhoneIcon class="size-6 rotate-[135deg] text-white" />
              </button>
              <span class="text-[11px] text-slate-400">{{ __('Decline') }}</span>
            </div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- COLUMN 3: RIGHT (On the Call & Call Notes) -->
        <!-- ========================================== -->
        <div class="flex flex-col gap-5 lg:col-span-3">
          <!-- Top Card: ON THE CALL -->
          <div class="rounded-2xl border border-outline-gray-2 bg-surface-white p-5 shadow-xs dark:border-outline-gray-7 dark:bg-surface-gray-8">
            <div class="mb-3 flex items-center justify-between">
              <h4 class="text-xs font-bold tracking-wider text-ink-gray-7 uppercase dark:text-ink-gray-3">
                {{ __('ON THE CALL') }}
              </h4>
              <Badge variant="subtle" size="sm" class="bg-blue-50 text-blue-700 font-semibold dark:bg-blue-950/40 dark:text-blue-300">
                {{ __('Cold Reach') }}
              </Badge>
            </div>

            <div class="space-y-2.5 text-xs">
              <div class="flex items-center justify-between border-b border-outline-gray-1 pb-1.5 dark:border-outline-gray-7">
                <span class="text-ink-gray-5">{{ __('Company') }}</span>
                <span class="font-semibold text-ink-gray-9 dark:text-ink-white truncate max-w-[140px]">
                  {{ state.contact?.organization || activeProspectCompany || '—' }}
                </span>
              </div>
              <div class="flex items-center justify-between border-b border-outline-gray-1 pb-1.5 dark:border-outline-gray-7">
                <span class="text-ink-gray-5">{{ __('Phone') }}</span>
                <span class="font-mono text-ink-gray-8 dark:text-ink-gray-2">
                  {{ state.phoneNumber || inputNumber || '—' }}
                </span>
              </div>
              <div class="flex items-center justify-between border-b border-outline-gray-1 pb-1.5 dark:border-outline-gray-7">
                <span class="text-ink-gray-5">{{ __('Attempt') }}</span>
                <span class="font-semibold text-ink-gray-9 dark:text-ink-white">
                  {{ __('1st call') }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-ink-gray-5">{{ __('Local time') }}</span>
                <span class="font-semibold text-ink-gray-9 dark:text-ink-white">
                  {{ localTimeString }}
                </span>
              </div>
            </div>
          </div>

          <!-- Bottom Card: CALL NOTES • AUTO -->
          <div class="flex flex-col rounded-2xl border border-outline-gray-2 bg-surface-white p-5 shadow-xs dark:border-outline-gray-7 dark:bg-surface-gray-8">
            <div class="mb-3">
              <h4 class="text-xs font-bold tracking-wider text-ink-gray-5 uppercase">
                {{ __('CALL NOTES • AUTO') }}
              </h4>
            </div>

            <textarea
              ref="notesTextareaRef"
              v-model="callNotes"
              rows="7"
              :placeholder="__('Notes will appear here during the call...')"
              class="w-full resize-none rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:bg-surface-white focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white dark:focus:bg-surface-gray-9"
              @input="handleNotesInput"
            />
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import LucideHome from '~icons/lucide/home'
import LucideDelete from '~icons/lucide/delete'
import LucideMic from '~icons/lucide/mic'
import LucideMicOff from '~icons/lucide/mic-off'
import LucideFileText from '~icons/lucide/file-text'
import { Badge, Dropdown, call, toast } from 'frappe-ui'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useTelephonyCall } from '@/composables/useTelephonyCall'

const { state, isCallActive, initiateCall, endCall, toggleMute, sendDigit, updateNotes } = useTelephonyCall()

// State
const inputNumber = ref('')
const showInCallKeypad = ref(false)
const callNotes = ref('')
const notesTextareaRef = ref(null)
const loadingTasks = ref(false)
const taskNumbers = ref([])
const selectedTaskFilter = ref('All Assigned')

// Country code options
const countryCodes = [
  { code: '+91', iso: 'IN', label: 'India (+91)' },
  { code: '+1', iso: 'US', label: 'United States (+1)' },
  { code: '+44', iso: 'GB', label: 'United Kingdom (+44)' },
  { code: '+61', iso: 'AU', label: 'Australia (+61)' },
  { code: '+49', iso: 'DE', label: 'Germany (+49)' },
  { code: '+33', iso: 'FR', label: 'France (+33)' },
  { code: '+971', iso: 'AE', label: 'UAE (+971)' },
  { code: '+65', iso: 'SG', label: 'Singapore (+65)' },
  { code: '+43', iso: 'AT', label: 'Austria (+43)' },
  { code: '+41', iso: 'CH', label: 'Switzerland (+41)' },
]
const selectedCountry = ref(countryCodes[0])

const countryCodeOptions = countryCodes.map((c) => ({
  label: `${c.iso} ${c.code} (${c.label.split(' ')[0]})`,
  onClick: () => {
    selectedCountry.value = c
  },
}))

// Caller IDs
const callerIds = ref([
  { label: 'GB United Kingdom • +44 7412 097737', number: '+44 7412 097737' },
  { label: 'US United States • +1 202 555 0143', number: '+1 202 555 0143' },
  { label: 'IN India • +91 98765 43210', number: '+91 98765 43210' },
])
const selectedCallerId = ref(callerIds.value[0])

const callerIdDropdownOptions = computed(() =>
  callerIds.value.map((cid) => ({
    label: cid.label,
    onClick: () => {
      selectedCallerId.value = cid
    },
  })),
)

// Keypad layout
const keypadKeys = [
  { digit: '1', letters: '' },
  { digit: '2', letters: 'ABC' },
  { digit: '3', letters: 'DEF' },
  { digit: '4', letters: 'GHI' },
  { digit: '5', letters: 'JKL' },
  { digit: '6', letters: 'MNO' },
  { digit: '7', letters: 'PQRS' },
  { digit: '8', letters: 'TUV' },
  { digit: '9', letters: 'WXYZ' },
  { digit: '*', letters: '' },
  { digit: '0', letters: '+' },
  { digit: '#', letters: '' },
]
const dtmfDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

// Active Prospect Display Meta
const activeProspectName = computed(() => {
  return state.contact?.full_name || 'Steve Iser'
})

const activeProspectCompany = computed(() => {
  return state.contact?.organization || 'Build Beyond'
})

// Avatar Colors Palette
const avatarColors = [
  '#f59e0b', // Amber
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#10b981', // Emerald
  '#3b82f6', // Blue
  '#ef4444', // Red
  '#14b8a6', // Teal
]

function getAvatarColor(name) {
  if (!name) return avatarColors[0]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return avatarColors[Math.abs(hash) % avatarColors.length]
}

function getInitials(name) {
  if (!name) return 'ST'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

// Local Time String
const localTimeString = computed(() => {
  const d = new Date()
  let hours = d.getHours()
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const ampm = hours >= 12 ? 'PM' : 'AM'
  hours = hours % 12 || 12
  return `${hours}:${minutes} ${ampm} (IST)`
})

// Task filter options
const taskFilterOptions = [
  { label: 'All Assigned', onClick: () => (selectedTaskFilter.value = 'All Assigned') },
  { label: 'To Do', onClick: () => (selectedTaskFilter.value = 'To Do') },
  { label: 'In Progress', onClick: () => (selectedTaskFilter.value = 'In Progress') },
  { label: 'Pending', onClick: () => (selectedTaskFilter.value = 'Pending') },
  { label: 'Follow up', onClick: () => (selectedTaskFilter.value = 'Follow up') },
  { label: 'Callback', onClick: () => (selectedTaskFilter.value = 'Callback') },
  { label: 'Not Interested', onClick: () => (selectedTaskFilter.value = 'Not Interested') },
]

const currentTaskFilterLabel = computed(() => selectedTaskFilter.value)

const filteredTaskNumbers = computed(() => {
  if (selectedTaskFilter.value === 'All Assigned') {
    return taskNumbers.value
  }
  return taskNumbers.value.filter((t) => t.status === selectedTaskFilter.value)
})

function pressKeypad(digit) {
  if (isCallActive.value) {
    sendDigit(digit)
  } else {
    inputNumber.value += digit
  }
}

function backspaceDigit() {
  if (!inputNumber.value) return
  inputNumber.value = inputNumber.value.slice(0, -1)
}

function handleCallButton(e) {
  e?.preventDefault?.()
  e?.stopPropagation?.()
  if (isCallActive.value) return
  let number = inputNumber.value ? inputNumber.value.trim() : ''
  if (!number) {
    toast.error(__('Please enter a phone number to call.'))
    return
  }

  // Prepend country code if not present
  if (!number.startsWith('+')) {
    number = selectedCountry.value.code + number.replace(/^0+/, '')
  }

  initiateCall(number, {
    full_name: activeProspectName.value,
    organization: activeProspectCompany.value,
  })
}

function dialProspect(item, e) {
  e?.preventDefault?.()
  e?.stopPropagation?.()
  const phone = item.mobile_no || item.phone
  if (!phone) {
    toast.error(__('No phone number available for this prospect.'))
    return
  }
  inputNumber.value = phone
  initiateCall(phone, {
    full_name: item.contact_name,
    organization: item.organization,
    designation: item.designation,
    name: item.name,
  })
}

function focusNotesTextarea() {
  notesTextareaRef.value?.focus?.()
}

let notesTimeout = null
function handleNotesInput() {
  if (notesTimeout) clearTimeout(notesTimeout)
  notesTimeout = setTimeout(() => {
    updateNotes(callNotes.value)
  }, 400)
}

// Fetch assigned tasks with phone numbers
async function fetchTasks() {
  loadingTasks.value = true
  try {
    const res = await call('crm.api.daily_allocation.get_allocated_tasks', {
      user: window.frappe?.session?.user || undefined,
      as_dict: 1,
      limit: 100,
    })

    const rows = Array.isArray(res) ? res : res?.tasks || []
    taskNumbers.value = rows.filter(
      (r) => (r.mobile_no && r.mobile_no.trim()) || (r.phone && r.phone.trim()),
    )

    // Pre-populate Caller ID if user has one configured
    try {
      const userTwilio = await call('frappe.client.get_value', {
        doctype: 'CRM Telephony Agent',
        filters: { user: window.frappe?.session?.user || '' },
        fieldname: 'twilio_number',
      })
      if (userTwilio?.message?.twilio_number) {
        const num = userTwilio.message.twilio_number
        callerIds.value.unshift({
          label: `Agent Twilio • ${num}`,
          number: num,
        })
        selectedCallerId.value = callerIds.value[0]
      }
    } catch (e) {
      // ignore
    }
  } catch (err) {
    console.error('Failed to fetch assigned task numbers:', err)
  } finally {
    loadingTasks.value = false
  }
}

onMounted(() => {
  fetchTasks()
})

onBeforeUnmount(() => {
  if (notesTimeout) clearTimeout(notesTimeout)
})
</script>
