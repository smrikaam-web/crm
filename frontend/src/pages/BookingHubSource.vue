<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Header -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-6 py-4 dark:border-outline-gray-7">
      <div class="flex items-center gap-3">
        <router-link
          to="/booking-hub"
          class="flex size-9 items-center justify-center rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-surface-gray-7 dark:text-ink-gray-3 dark:hover:bg-surface-gray-8"
        >
          ←
        </router-link>
        <div>
          <div class="flex items-center gap-2.5">
            <h1 class="text-lg font-bold text-ink-gray-9 dark:text-ink-white">
              {{ source ? source.source_name : sourceId }}
            </h1>
            <span
              v-if="source"
              class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
              :class="statusBadgeClass(source.connection_status)"
            >
              <span class="size-1.5 rounded-full" :class="statusDotClass(source.connection_status)"></span>
              {{ source.connection_status }}
            </span>
          </div>
          <p class="text-xs text-ink-gray-5">
            {{ source ? '@' + source.domain : sourceId }} • {{ source?.website_type || 'Website Source' }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 shadow-sm hover:bg-gray-50 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
          @click="showSetupModal = true"
        >
          <svg class="size-3.5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>{{ __('Integration Setup') }}</span>
        </button>
        <button
          type="button"
          class="flex size-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 shadow-sm hover:bg-gray-50 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
          @click="fetchData"
        >
          <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>
    </header>

    <div class="space-y-6 p-6">
      <!-- Top Source Metric Cards -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="text-xs font-semibold text-gray-500">{{ __('Total Bookings') }}</div>
          <div class="mt-1 text-2xl font-bold text-gray-900 dark:text-ink-white">{{ source?.total_bookings || bookingsTotal }}</div>
        </div>
        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="text-xs font-semibold text-gray-500">{{ __('New Bookings') }}</div>
          <div class="mt-1 text-2xl font-bold text-emerald-600">{{ source?.new_bookings || 0 }}</div>
        </div>
        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="text-xs font-semibold text-gray-500">{{ __('Credential Reference') }}</div>
          <div class="mt-1 truncate font-mono text-xs text-gray-700 dark:text-ink-gray-3">{{ source?.credential_reference || 'N/A' }}</div>
        </div>
        <div class="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="text-xs font-semibold text-gray-500">{{ __('Last Successful Booking') }}</div>
          <div class="mt-1 text-xs font-medium text-gray-700 dark:text-ink-gray-3">{{ source?.last_successful_booking || 'No bookings recorded' }}</div>
        </div>
      </div>

      <!-- Bookings Table Section -->
      <div class="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
        <!-- Controls Bar -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 p-4 dark:border-surface-gray-7">
          <div class="text-base font-bold text-gray-900 dark:text-ink-white">
            {{ __('Bookings') }}
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <!-- Search -->
            <div class="relative flex items-center">
              <span class="absolute left-3 text-gray-400">
                <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search bookings..."
                class="w-56 rounded-xl border border-gray-200 bg-gray-50/50 py-1.5 pl-9 pr-3 text-xs text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
                @input="onSearch"
              />
            </div>

            <!-- Status Filter -->
            <select
              v-model="statusFilter"
              class="rounded-xl border border-gray-200 bg-gray-50/50 px-3 py-1.5 text-xs font-medium text-gray-700 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
              @change="fetchBookings"
            >
              <option value="All">{{ __('All Statuses') }}</option>
              <option value="New">{{ __('New') }}</option>
              <option value="Upcoming">{{ __('Upcoming') }}</option>
              <option value="Confirmed">{{ __('Confirmed') }}</option>
              <option value="Completed">{{ __('Completed') }}</option>
              <option value="Cancelled">{{ __('Cancelled') }}</option>
              <option value="Rescheduled">{{ __('Rescheduled') }}</option>
            </select>
          </div>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-gray-100 bg-gray-50/50 text-[11px] font-bold uppercase tracking-wider text-gray-400 dark:border-surface-gray-7 dark:bg-surface-gray-9">
              <tr>
                <th class="py-3 pl-4 pr-2">
                  <input type="checkbox" class="rounded border-gray-300" />
                </th>
                <th class="px-3 py-3">{{ __('CUSTOMER NAME') }}</th>
                <th class="px-3 py-3">{{ __('COMPANY') }}</th>
                <th class="px-3 py-3">{{ __('EMAIL') }}</th>
                <th class="px-3 py-3">{{ __('PHONE') }}</th>
                <th class="px-3 py-3">{{ __('APPOINTMENT DATE') }}</th>
                <th class="px-3 py-3">{{ __('TIME') }}</th>
                <th class="px-3 py-3">{{ __('STATUS') }}</th>
                <th class="py-3 pl-3 pr-4 text-right">{{ __('ACTIONS') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-surface-gray-7">
              <tr
                v-for="b in bookings"
                :key="b.name"
                class="transition hover:bg-gray-50/60 dark:hover:bg-surface-gray-7/40"
              >
                <td class="py-3 pl-4 pr-2">
                  <input type="checkbox" class="rounded border-gray-300" />
                </td>
                <td class="px-3 py-3 font-semibold text-gray-900 dark:text-ink-white">
                  {{ b.customer_name }}
                </td>
                <td class="px-3 py-3 text-gray-600 dark:text-ink-gray-3">
                  {{ b.company_name || '—' }}
                </td>
                <td class="px-3 py-3 text-gray-600 dark:text-ink-gray-3">
                  {{ b.email }}
                </td>
                <td class="px-3 py-3 text-gray-600 dark:text-ink-gray-3">
                  {{ b.phone || '—' }}
                </td>
                <td class="px-3 py-3 text-gray-700 dark:text-ink-gray-3">
                  <div class="flex items-center gap-1.5">
                    <svg class="size-3.5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                    <span>{{ b.appointment_date || '—' }}</span>
                  </div>
                </td>
                <td class="px-3 py-3 text-gray-700 dark:text-ink-gray-3">
                  <div class="flex items-center gap-1.5">
                    <svg class="size-3.5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    <span>{{ b.appointment_time || '—' }}</span>
                  </div>
                </td>
                <td class="px-3 py-3">
                  <span
                    class="inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                    :class="statusBadgeClass(b.booking_status)"
                  >
                    {{ b.booking_status }}
                  </span>
                </td>
                <td class="py-3 pl-3 pr-4 text-right">
                  <div class="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      class="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-surface-gray-7"
                      @click="openBookingDetail(b.name)"
                    >
                      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!bookings.length">
                <td colspan="9" class="py-8 text-center text-xs text-gray-400">
                  {{ __('No bookings found for this website source.') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 p-4 dark:border-surface-gray-7">
          <div class="flex items-center gap-2">
            <button
              v-for="size in [20, 50, 100]"
              :key="size"
              type="button"
              class="rounded-lg px-2.5 py-1 text-xs font-semibold transition"
              :class="pageSize === size ? 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300' : 'text-gray-500 hover:bg-gray-100'"
              @click="changePageSize(size)"
            >
              {{ size }}
            </button>
          </div>

          <div class="text-xs text-gray-500">
            {{ bookings.length }} of {{ bookingsTotal }}
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <BookingDetailModal
      v-model="showDetailModal"
      :bookingId="selectedBookingId"
      @updated="fetchBookings"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import BookingDetailModal from '@/components/Modals/BookingDetailModal.vue'

const route = useRoute()
const sourceId = ref(route.params.sourceId || '')

const source = ref(null)
const bookings = ref([])
const bookingsTotal = ref(0)
const pageSize = ref(20)
const statusFilter = ref('All')
const searchQuery = ref('')
const showSetupModal = ref(false)
const showDetailModal = ref(false)
const selectedBookingId = ref('')

onMounted(() => {
  fetchData()
})

async function fetchData() {
  await Promise.all([fetchSource(), fetchBookings()])
}

async function fetchSource() {
  try {
    const res = await call('crm.api.booking_hub.get_booking_hub_summary')
    if (res && res.sources) {
      source.value = res.sources.find((s) => s.source_id === sourceId.value) || null
    }
  } catch (err) {
    console.error('Error fetching source:', err)
  }
}

async function fetchBookings() {
  try {
    const res = await call('crm.api.booking_hub.get_bookings', {
      source_id: sourceId.value,
      status: statusFilter.value,
      search: searchQuery.value,
      page_length: pageSize.value,
      start: 0,
    })
    if (res) {
      bookings.value = res.bookings || []
      bookingsTotal.value = res.total_count || 0
    }
  } catch (err) {
    console.error('Error fetching bookings:', err)
  }
}

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchBookings()
  }, 300)
}

function changePageSize(size) {
  pageSize.value = size
  fetchBookings()
}

function openBookingDetail(id) {
  selectedBookingId.value = id
  showDetailModal.value = true
}

function statusBadgeClass(status) {
  switch (status) {
    case 'Connected':
    case 'Confirmed':
      return 'bg-emerald-50 text-emerald-700'
    case 'New':
      return 'bg-sky-50 text-sky-700'
    case 'Upcoming':
      return 'bg-purple-50 text-purple-700'
    case 'Completed':
      return 'bg-green-100 text-green-800'
    case 'Cancelled':
    case 'Connection Failed':
      return 'bg-rose-50 text-rose-700'
    case 'Rescheduled':
      return 'bg-amber-50 text-amber-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function statusDotClass(status) {
  switch (status) {
    case 'Connected':
      return 'bg-emerald-500'
    case 'Testing':
      return 'bg-blue-500'
    case 'Connection Failed':
      return 'bg-rose-500'
    default:
      return 'bg-amber-500'
  }
}
</script>
