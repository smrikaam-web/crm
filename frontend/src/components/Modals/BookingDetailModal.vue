<template>
  <Dialog v-model:open="isOpen" bare>
    <template #default>
      <div class="relative w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-surface-gray-9 dark:text-ink-white">
        <!-- Close button top right -->
        <button
          type="button"
          class="absolute right-4 top-4 z-10 flex size-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-surface-gray-8 dark:hover:text-ink-white"
          @click="closeModal"
        >
          <span class="text-xl leading-none">&times;</span>
        </button>

        <div v-if="loading" class="flex h-64 items-center justify-center">
          <svg class="size-8 animate-spin text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25" />
            <path d="M4 12a8 8 0 018-8v8H4z" class="opacity-75" fill="currentColor" />
          </svg>
        </div>

        <div v-else-if="booking" class="max-h-[90vh] overflow-y-auto p-6">
          <!-- Header -->
          <div class="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-4 dark:border-surface-gray-8">
            <div class="flex items-center gap-3">
              <div class="flex size-11 items-center justify-center rounded-xl bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400">
                <svg class="size-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="text-lg font-bold text-gray-900 dark:text-ink-white">
                    {{ booking.customer_name }}
                  </h2>
                  <span
                    class="rounded-md px-2 py-0.5 text-xs font-semibold"
                    :class="sourceBadgeClass(booking.source_name)"
                  >
                    {{ booking.source_name || booking.source }}
                  </span>
                </div>
                <div class="flex items-center gap-2 text-xs text-gray-500">
                  <span class="font-mono font-medium">{{ booking.name }}</span>
                  <span v-if="booking.company_name">• {{ booking.company_name }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span
                class="rounded-full px-3 py-1 text-xs font-semibold"
                :class="statusBadgeClass(booking.booking_status)"
              >
                {{ booking.booking_status }}
              </span>
            </div>
          </div>

          <!-- Quick Action Bar -->
          <div class="mb-5 flex flex-wrap items-center gap-2 rounded-xl bg-gray-50 p-2.5 dark:bg-surface-gray-8">
            <span class="text-xs font-semibold text-gray-500 dark:text-ink-gray-4">{{ __('Actions:') }}</span>
            <button
              v-if="booking.booking_status !== 'Confirmed'"
              type="button"
              class="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700"
              @click="changeStatus('Confirmed')"
            >
              ✓ {{ __('Confirm') }}
            </button>
            <button
              type="button"
              class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700"
              @click="showRescheduleForm = !showRescheduleForm"
            >
              📅 {{ __('Reschedule') }}
            </button>
            <button
              v-if="booking.booking_status !== 'Completed'"
              type="button"
              class="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
              @click="changeStatus('Completed')"
            >
              ★ {{ __('Complete') }}
            </button>
            <button
              v-if="booking.booking_status !== 'Cancelled'"
              type="button"
              class="rounded-lg bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 dark:bg-rose-950/50 dark:text-rose-300"
              @click="changeStatus('Cancelled')"
            >
              ✕ {{ __('Cancel') }}
            </button>
          </div>

          <!-- Inline Reschedule Box -->
          <div v-if="showRescheduleForm" class="mb-5 rounded-xl border border-blue-200 bg-blue-50/50 p-4 dark:border-blue-900/50 dark:bg-blue-950/30">
            <h4 class="mb-2 text-xs font-bold text-blue-900 dark:text-blue-300">{{ __('Reschedule Appointment') }}</h4>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="text-[11px] font-semibold text-gray-600 dark:text-ink-gray-4">{{ __('New Date') }}</label>
                <input
                  v-model="rescheduleData.date"
                  type="date"
                  class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
                />
              </div>
              <div>
                <label class="text-[11px] font-semibold text-gray-600 dark:text-ink-gray-4">{{ __('New Time') }}</label>
                <input
                  v-model="rescheduleData.time"
                  type="text"
                  placeholder="e.g. 11:30 AM"
                  class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
                />
              </div>
            </div>
            <div class="mt-2">
              <label class="text-[11px] font-semibold text-gray-600 dark:text-ink-gray-4">{{ __('Reason (Optional)') }}</label>
              <input
                v-model="rescheduleData.reason"
                type="text"
                placeholder="Client requested alternate slot"
                class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
              />
            </div>
            <div class="mt-3 flex justify-end gap-2">
              <button
                type="button"
                class="rounded-lg border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-white"
                @click="showRescheduleForm = false"
              >
                {{ __('Cancel') }}
              </button>
              <button
                type="button"
                :disabled="savingReschedule"
                class="rounded-lg bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700"
                @click="submitReschedule"
              >
                {{ savingReschedule ? __('Saving...') : __('Save Reschedule') }}
              </button>
            </div>
          </div>

          <!-- Information Grid -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <!-- Email -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Email') }}</div>
              <a
                :href="'mailto:' + booking.email"
                class="mt-0.5 block truncate text-xs font-semibold text-indigo-600 hover:underline"
              >
                {{ booking.email }}
              </a>
            </div>

            <!-- Phone -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Phone') }}</div>
              <a
                v-if="booking.phone"
                :href="'tel:' + booking.phone"
                class="mt-0.5 block truncate text-xs font-semibold text-gray-800 hover:text-indigo-600 dark:text-ink-white"
              >
                {{ booking.phone }}
              </a>
              <span v-else class="text-xs text-gray-400">{{ __('Not provided') }}</span>
            </div>

            <!-- Appointment Date & Time -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Appointment Slot') }}</div>
              <div class="mt-0.5 flex items-center gap-1.5 text-xs font-bold text-gray-900 dark:text-ink-white">
                <span>{{ booking.appointment_date || 'Date TBD' }}</span>
                <span>•</span>
                <span>{{ booking.appointment_time || 'Time TBD' }}</span>
                <span v-if="booking.timezone" class="text-[11px] font-normal text-gray-500">({{ booking.timezone }})</span>
              </div>
            </div>

            <!-- Interested Service -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Interested Service') }}</div>
              <div class="mt-0.5 truncate text-xs font-semibold text-gray-800 dark:text-ink-white">
                {{ booking.interested_service || 'General Inquiry' }}
              </div>
            </div>

            <!-- Assigned CRM User -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Assigned To') }}</div>
              <div class="mt-1 flex items-center justify-between">
                <span class="text-xs font-semibold text-gray-800 dark:text-ink-white">
                  {{ booking.assigned_to || 'Unassigned' }}
                </span>
                <button
                  type="button"
                  class="text-[11px] font-semibold text-indigo-600 hover:underline"
                  @click="promptAssign"
                >
                  {{ __('Change') }}
                </button>
              </div>
            </div>

            <!-- Submission URL -->
            <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-8 dark:bg-surface-gray-8/50">
              <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Submission URL / Submitted At') }}</div>
              <div class="mt-0.5 truncate text-xs text-gray-600 dark:text-ink-gray-3">
                <a
                  v-if="booking.page_url"
                  :href="booking.page_url"
                  target="_blank"
                  class="text-indigo-600 hover:underline"
                >
                  {{ booking.page_url }}
                </a>
                <span v-else>{{ __('Direct / Website Form') }}</span>
              </div>
              <div class="text-[10px] text-gray-400">
                {{ booking.submitted_at || booking.creation }}
              </div>
            </div>
          </div>

          <!-- Customer Message -->
          <div v-if="booking.message" class="mt-4 rounded-xl border border-gray-200 bg-gray-50/50 p-3.5 dark:border-surface-gray-7 dark:bg-surface-gray-8">
            <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-gray-500">{{ __('Message from Visitor') }}</div>
            <p class="whitespace-pre-wrap text-xs leading-relaxed text-gray-800 dark:text-ink-gray-2">{{ booking.message }}</p>
          </div>

          <!-- Internal Notes Section -->
          <div class="mt-4 rounded-xl border border-gray-200 bg-white p-3.5 dark:border-surface-gray-7 dark:bg-surface-gray-8">
            <div class="mb-1 flex items-center justify-between">
              <span class="text-xs font-bold text-gray-800 dark:text-ink-white">{{ __('Internal Team Notes') }}</span>
              <button
                type="button"
                :disabled="savingNote"
                class="rounded-lg bg-gray-900 px-3 py-1 text-xs font-semibold text-white hover:bg-black disabled:opacity-50"
                @click="saveInternalNote"
              >
                {{ savingNote ? __('Saving...') : __('Save Note') }}
              </button>
            </div>
            <textarea
              v-model="newNote"
              rows="2"
              placeholder="Add internal notes about this booking, client call discussion, follow-up actions..."
              class="w-full rounded-lg border border-gray-200 p-2 text-xs text-gray-800 focus:border-indigo-500 focus:outline-none dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
            ></textarea>
            <div v-if="booking.internal_notes" class="mt-2 text-xs text-gray-600 dark:text-ink-gray-4">
              <span class="font-semibold">{{ __('Previous Notes:') }}</span>
              <p class="whitespace-pre-wrap rounded bg-gray-50 p-2 font-mono text-[11px] text-gray-700 dark:bg-surface-gray-9 dark:text-ink-gray-3">{{ booking.internal_notes }}</p>
            </div>
          </div>

          <!-- Activity History -->
          <div class="mt-5 border-t border-gray-100 pt-4 dark:border-surface-gray-8">
            <h4 class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-500">
              {{ __('Activity History') }} ({{ activities.length }})
            </h4>
            <div v-if="activities.length" class="space-y-3">
              <div
                v-for="act in activities"
                :key="act.name"
                class="flex items-start gap-3 rounded-lg border border-gray-100 bg-gray-50/60 p-2.5 dark:border-surface-gray-8 dark:bg-surface-gray-8/50"
              >
                <div class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[10px] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                  ●
                </div>
                <div class="flex-1">
                  <div class="flex items-center justify-between text-xs font-semibold text-gray-900 dark:text-ink-white">
                    <span>{{ act.subject }}</span>
                    <span class="text-[10px] font-normal text-gray-400">{{ act.timestamp }}</span>
                  </div>
                  <div v-if="act.details" class="text-xs text-gray-600 dark:text-ink-gray-4">
                    {{ act.details }}
                  </div>
                  <div class="text-[10px] text-gray-400">
                    {{ __('By:') }} {{ act.by_user || 'System' }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-xs text-gray-400">
              {{ __('No activity logged yet.') }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { call, Dialog } from 'frappe-ui'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  bookingId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'updated'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const loading = ref(false)
const booking = ref(null)
const activities = ref([])
const showRescheduleForm = ref(false)
const savingReschedule = ref(false)
const savingNote = ref(false)
const newNote = ref('')

const rescheduleData = reactive({
  date: '',
  time: '',
  reason: '',
})

watch(
  () => props.bookingId,
  (newId) => {
    if (newId && props.modelValue) {
      loadBooking()
    }
  }
)

watch(
  () => props.modelValue,
  (open) => {
    if (open && props.bookingId) {
      loadBooking()
    }
  }
)

async function loadBooking() {
  if (!props.bookingId) return
  loading.value = true
  try {
    const res = await call('crm.api.booking_hub.get_booking_detail', {
      booking_reference: props.bookingId,
    })
    if (res && res.booking) {
      booking.value = res.booking
      activities.value = res.activities || []
      rescheduleData.date = res.booking.appointment_date || ''
      rescheduleData.time = res.booking.appointment_time || ''
    }
  } catch (err) {
    console.error('Error loading booking detail:', err)
  } finally {
    loading.value = false
  }
}

function closeModal() {
  isOpen.value = false
}

async function changeStatus(newStatus) {
  if (!booking.value) return
  try {
    await call('crm.api.booking_hub.update_booking_status', {
      booking_reference: booking.value.name,
      status: newStatus,
    })
    emit('updated')
    loadBooking()
  } catch (err) {
    alert('Failed to update status: ' + err.message)
  }
}

async function submitReschedule() {
  if (!rescheduleData.date) {
    alert('Please pick a date')
    return
  }
  savingReschedule.value = true
  try {
    await call('crm.api.booking_hub.reschedule_booking', {
      booking_reference: booking.value.name,
      new_date: rescheduleData.date,
      new_time: rescheduleData.time,
      reason: rescheduleData.reason,
    })
    showRescheduleForm.value = false
    emit('updated')
    loadBooking()
  } catch (err) {
    alert('Failed to reschedule: ' + err.message)
  } finally {
    savingReschedule.value = false
  }
}

async function saveInternalNote() {
  if (!newNote.value?.trim()) return
  savingNote.value = true
  try {
    await call('crm.api.booking_hub.add_booking_note', {
      booking_reference: booking.value.name,
      note: newNote.value.trim(),
    })
    newNote.value = ''
    emit('updated')
    loadBooking()
  } catch (err) {
    alert('Failed to add note: ' + err.message)
  } finally {
    savingNote.value = false
  }
}

async function promptAssign() {
  const userEmail = prompt('Enter user email to assign this booking:', booking.value?.assigned_to || '')
  if (userEmail !== null) {
    try {
      await call('crm.api.booking_hub.assign_booking', {
        booking_reference: booking.value.name,
        assigned_to: userEmail.trim(),
      })
      emit('updated')
      loadBooking()
    } catch (err) {
      alert('Failed to assign: ' + err.message)
    }
  }
}

function sourceBadgeClass(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('smrikaam')) {
    return 'bg-purple-100 text-purple-800 border border-purple-200'
  }
  if (n.includes('bitxhift')) {
    return 'bg-blue-100 text-blue-800 border border-blue-200'
  }
  return 'bg-gray-100 text-gray-800 border border-gray-200'
}

function statusBadgeClass(status) {
  switch (status) {
    case 'New':
      return 'bg-sky-50 text-sky-700'
    case 'Upcoming':
      return 'bg-purple-50 text-purple-700'
    case 'Confirmed':
      return 'bg-emerald-50 text-emerald-700'
    case 'Completed':
      return 'bg-green-100 text-green-800'
    case 'Cancelled':
      return 'bg-rose-50 text-rose-700'
    case 'Rescheduled':
      return 'bg-amber-50 text-amber-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}
</script>
