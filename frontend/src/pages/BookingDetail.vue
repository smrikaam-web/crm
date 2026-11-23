<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-outline-gray-2 px-6 py-4 dark:border-outline-gray-7">
      <div class="flex items-center gap-3">
        <router-link
          to="/booking-hub"
          class="flex size-8 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-surface-gray-7 dark:text-ink-gray-3 dark:hover:bg-surface-gray-8"
        >
          ←
        </router-link>
        <div>
          <h1 class="text-lg font-bold text-ink-gray-9 dark:text-ink-white">
            {{ __('Booking Details') }}
          </h1>
          <p class="text-xs text-ink-gray-5">
            {{ bookingId }}
          </p>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <svg class="size-8 animate-spin text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25" />
          <path d="M4 12a8 8 0 018-8v8H4z" class="opacity-75" fill="currentColor" />
        </svg>
      </div>

      <div v-else-if="booking" class="mx-auto max-w-3xl space-y-6">
        <!-- Top Card -->
        <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-4 dark:border-surface-gray-7">
            <div class="flex items-center gap-3">
              <div class="flex size-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400">
                <svg class="size-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="text-xl font-bold text-gray-900 dark:text-ink-white">
                    {{ booking.customer_name }}
                  </h2>
                  <span class="rounded-md bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700">
                    {{ booking.source_name || booking.source }}
                  </span>
                </div>
                <div class="text-xs text-gray-500">
                  {{ booking.name }} <span v-if="booking.company_name">• {{ booking.company_name }}</span>
                </div>
              </div>
            </div>

            <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(booking.booking_status)">
              {{ booking.booking_status }}
            </span>
          </div>

          <!-- Actions -->
          <div class="mt-4 flex flex-wrap items-center gap-2">
            <button
              v-if="booking.booking_status !== 'Confirmed'"
              type="button"
              class="rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
              @click="changeStatus('Confirmed')"
            >
              ✓ {{ __('Confirm Appointment') }}
            </button>
            <button
              type="button"
              class="rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
              @click="showReschedule = !showReschedule"
            >
              📅 {{ __('Reschedule') }}
            </button>
            <button
              v-if="booking.booking_status !== 'Completed'"
              type="button"
              class="rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
              @click="changeStatus('Completed')"
            >
              ★ {{ __('Mark Completed') }}
            </button>
            <button
              v-if="booking.booking_status !== 'Cancelled'"
              type="button"
              class="rounded-lg bg-rose-50 px-3.5 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100"
              @click="changeStatus('Cancelled')"
            >
              ✕ {{ __('Cancel Appointment') }}
            </button>
          </div>

          <!-- Reschedule Form -->
          <div v-if="showReschedule" class="mt-4 rounded-xl border border-blue-200 bg-blue-50/50 p-4">
            <h4 class="mb-2 text-xs font-bold text-blue-900">{{ __('Reschedule Appointment') }}</h4>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="text-[11px] font-semibold text-gray-600">{{ __('New Date') }}</label>
                <input
                  v-model="rescheduleData.date"
                  type="date"
                  class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900"
                />
              </div>
              <div>
                <label class="text-[11px] font-semibold text-gray-600">{{ __('New Time') }}</label>
                <input
                  v-model="rescheduleData.time"
                  type="text"
                  placeholder="e.g. 11:30 AM"
                  class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900"
                />
              </div>
            </div>
            <div class="mt-2">
              <label class="text-[11px] font-semibold text-gray-600">{{ __('Reason (Optional)') }}</label>
              <input
                v-model="rescheduleData.reason"
                type="text"
                placeholder="Reason for reschedule..."
                class="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2 text-xs text-gray-900"
              />
            </div>
            <div class="mt-3 flex justify-end gap-2">
              <button
                type="button"
                class="rounded-lg border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-white"
                @click="showReschedule = false"
              >
                {{ __('Cancel') }}
              </button>
              <button
                type="button"
                class="rounded-lg bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700"
                @click="submitReschedule"
              >
                {{ __('Save Reschedule') }}
              </button>
            </div>
          </div>

          <!-- Info Fields -->
          <div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Email') }}</span>
              <a :href="'mailto:' + booking.email" class="mt-0.5 block text-xs font-bold text-indigo-600 hover:underline">
                {{ booking.email }}
              </a>
            </div>
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Phone') }}</span>
              <div class="mt-0.5 text-xs font-bold text-gray-900 dark:text-ink-white">
                {{ booking.phone || 'N/A' }}
              </div>
            </div>
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Appointment Slot') }}</span>
              <div class="mt-0.5 text-xs font-bold text-gray-900 dark:text-ink-white">
                {{ booking.appointment_date }} at {{ booking.appointment_time }}
                <span v-if="booking.timezone" class="text-gray-500">({{ booking.timezone }})</span>
              </div>
            </div>
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Service') }}</span>
              <div class="mt-0.5 text-xs font-bold text-gray-900 dark:text-ink-white">
                {{ booking.interested_service || 'General Inquiry' }}
              </div>
            </div>
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Assigned To') }}</span>
              <div class="mt-0.5 flex items-center justify-between text-xs font-bold text-gray-900 dark:text-ink-white">
                <span>{{ booking.assigned_to || 'Unassigned' }}</span>
                <button type="button" class="text-[11px] text-indigo-600 hover:underline" @click="promptAssign">
                  {{ __('Reassign') }}
                </button>
              </div>
            </div>
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{{ __('Submission Details') }}</span>
              <div class="mt-0.5 text-xs text-gray-600">
                <span>{{ booking.page_url || 'Website Form' }}</span>
                <div class="text-[10px] text-gray-400">{{ booking.submitted_at || booking.creation }}</div>
              </div>
            </div>
          </div>

          <!-- Message -->
          <div v-if="booking.message" class="mt-4 rounded-xl bg-gray-50 p-3.5 dark:bg-surface-gray-9">
            <span class="text-[11px] font-bold uppercase tracking-wider text-gray-400">{{ __('Message from Visitor') }}</span>
            <p class="mt-1 text-xs text-gray-800 dark:text-ink-gray-2">{{ booking.message }}</p>
          </div>
        </div>

        <!-- Notes -->
        <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-sm font-bold text-gray-900 dark:text-ink-white">{{ __('Internal Team Notes') }}</h3>
            <button
              type="button"
              class="rounded-lg bg-gray-900 px-3 py-1 text-xs font-semibold text-white hover:bg-black"
              @click="saveInternalNote"
            >
              {{ __('Save Note') }}
            </button>
          </div>
          <textarea
            v-model="newNote"
            rows="2"
            placeholder="Add internal discussion note..."
            class="w-full rounded-xl border border-gray-200 p-2.5 text-xs text-gray-900 dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
          ></textarea>
          <div v-if="booking.internal_notes" class="mt-3">
            <span class="text-[11px] font-semibold text-gray-500">{{ __('Notes Log:') }}</span>
            <pre class="mt-1 whitespace-pre-wrap rounded-lg bg-gray-50 p-3 font-mono text-[11px] text-gray-700 dark:bg-surface-gray-9 dark:text-ink-gray-3">{{ booking.internal_notes }}</pre>
          </div>
        </div>

        <!-- Activity History -->
        <div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <h3 class="mb-4 text-sm font-bold text-gray-900 dark:text-ink-white">
            {{ __('Activity History') }} ({{ activities.length }})
          </h3>
          <div v-if="activities.length" class="space-y-3">
            <div
              v-for="act in activities"
              :key="act.name"
              class="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-surface-gray-7 dark:bg-surface-gray-9"
            >
              <div class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[10px] text-indigo-600">
                ●
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between text-xs font-semibold text-gray-900 dark:text-ink-white">
                  <span>{{ act.subject }}</span>
                  <span class="text-[10px] text-gray-400">{{ act.timestamp }}</span>
                </div>
                <div v-if="act.details" class="mt-0.5 text-xs text-gray-600 dark:text-ink-gray-4">
                  {{ act.details }}
                </div>
                <div class="text-[10px] text-gray-400">
                  {{ __('By:') }} {{ act.by_user || 'System' }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-xs text-gray-400">
            {{ __('No activity recorded yet.') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'

const route = useRoute()
const bookingId = ref(route.params.bookingId || '')

const loading = ref(false)
const booking = ref(null)
const activities = ref([])
const showReschedule = ref(false)
const newNote = ref('')

const rescheduleData = reactive({
  date: '',
  time: '',
  reason: '',
})

onMounted(() => {
  if (bookingId.value) {
    loadBooking()
  }
})

async function loadBooking() {
  loading.value = true
  try {
    const res = await call('crm.api.booking_hub.get_booking_detail', {
      booking_reference: bookingId.value,
    })
    if (res && res.booking) {
      booking.value = res.booking
      activities.value = res.activities || []
      rescheduleData.date = res.booking.appointment_date || ''
      rescheduleData.time = res.booking.appointment_time || ''
    }
  } catch (err) {
    console.error('Error loading booking:', err)
  } finally {
    loading.value = false
  }
}

async function changeStatus(status) {
  try {
    await call('crm.api.booking_hub.update_booking_status', {
      booking_reference: booking.value.name,
      status,
    })
    loadBooking()
  } catch (err) {
    alert('Failed to update: ' + err.message)
  }
}

async function submitReschedule() {
  try {
    await call('crm.api.booking_hub.reschedule_booking', {
      booking_reference: booking.value.name,
      new_date: rescheduleData.date,
      new_time: rescheduleData.time,
      reason: rescheduleData.reason,
    })
    showReschedule.value = false
    loadBooking()
  } catch (err) {
    alert('Failed to reschedule: ' + err.message)
  }
}

async function saveInternalNote() {
  if (!newNote.value?.trim()) return
  try {
    await call('crm.api.booking_hub.add_booking_note', {
      booking_reference: booking.value.name,
      note: newNote.value.trim(),
    })
    newNote.value = ''
    loadBooking()
  } catch (err) {
    alert('Failed to save note: ' + err.message)
  }
}

async function promptAssign() {
  const email = prompt('Enter user email:', booking.value?.assigned_to || '')
  if (email !== null) {
    try {
      await call('crm.api.booking_hub.assign_booking', {
        booking_reference: booking.value.name,
        assigned_to: email.trim(),
      })
      loadBooking()
    } catch (err) {
      alert('Failed to assign: ' + err.message)
    }
  }
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
