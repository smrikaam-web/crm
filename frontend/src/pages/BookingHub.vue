<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- 1. Top Header -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-6 py-4 dark:border-outline-gray-7">
      <div class="flex items-center gap-3.5">
        <div class="flex size-11 items-center justify-center rounded-2xl border border-gray-200 bg-white text-gray-700 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white">
          <!-- Calendar Icon -->
          <svg class="size-5.5 text-gray-700 dark:text-ink-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-gray-900 dark:text-ink-white">
            {{ __('Booking Hub') }}
          </h1>
          <p class="text-xs text-gray-500 dark:text-ink-gray-4">
            {{ __('Centralized Website Appointment Management') }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2.5">
        <!-- Add Source Button -->
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-xl bg-gray-900 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-black"
          @click="showAddSourceModal = true"
        >
          <span>+</span>
          <span>{{ __('Add Source') }}</span>
        </button>

        <!-- Manage Sources Button -->
        <router-link
          to="/booking-hub/manage-sources"
          class="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white dark:hover:bg-surface-gray-7"
        >
          <svg class="size-3.5 text-gray-500 dark:text-ink-gray-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>{{ __('Manage Sources') }}</span>
        </router-link>

        <!-- Refresh Button -->
        <button
          type="button"
          :disabled="loading"
          class="flex size-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 shadow-sm transition hover:bg-gray-50 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white dark:hover:bg-surface-gray-7 disabled:opacity-50"
          @click="fetchData"
        >
          <svg class="size-4" :class="{ 'animate-spin': loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Main Body Area -->
    <div class="space-y-6 p-6">
      <!-- 2. Summary Metric Cards (5 Cards) -->
      <div class="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-5">
        <!-- Total Bookings -->
        <div class="flex items-center gap-3.5 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400">
            <svg class="size-5.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </div>
          <div>
            <div class="text-xs font-medium text-gray-500 dark:text-ink-gray-4">{{ __('Total Bookings') }}</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-ink-white">{{ metrics.total_bookings }}</div>
          </div>
        </div>

        <!-- New Bookings -->
        <div class="flex items-center gap-3.5 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
            <svg class="size-5.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <div class="text-xs font-medium text-gray-500 dark:text-ink-gray-4">{{ __('New Bookings') }}</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-ink-white">{{ metrics.new_bookings }}</div>
          </div>
        </div>

        <!-- Upcoming Appointments -->
        <div class="flex items-center gap-3.5 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-400">
            <svg class="size-5.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <div>
            <div class="text-xs font-medium text-gray-500 dark:text-ink-gray-4">{{ __('Upcoming Appointments') }}</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-ink-white">{{ metrics.upcoming_appointments }}</div>
          </div>
        </div>

        <!-- Completed -->
        <div class="flex items-center gap-3.5 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400">
            <svg class="size-5.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div>
            <div class="text-xs font-medium text-gray-500 dark:text-ink-gray-4">{{ __('Completed') }}</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-ink-white">{{ metrics.completed_appointments }}</div>
          </div>
        </div>

        <!-- Cancelled -->
        <div class="flex items-center gap-3.5 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-rose-50 text-rose-500 dark:bg-rose-950 dark:text-rose-400">
            <svg class="size-5.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <div>
            <div class="text-xs font-medium text-gray-500 dark:text-ink-gray-4">{{ __('Cancelled') }}</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-ink-white">{{ metrics.cancelled_appointments }}</div>
          </div>
        </div>
      </div>

      <!-- 3. Website Sources Section -->
      <div>
        <div class="mb-3">
          <h2 class="text-base font-bold text-gray-900 dark:text-ink-white">
            {{ __('Website Sources') }}
          </h2>
          <p class="text-xs text-gray-500 dark:text-ink-gray-4">
            {{ __('Manage and view appointment bookings from your websites') }}
          </p>
        </div>

        <!-- Source Cards Grid -->
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div
            v-for="s in sources"
            :key="s.source_id"
            class="group cursor-pointer rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition hover:border-gray-200 hover:shadow-md dark:border-surface-gray-7 dark:bg-surface-gray-8"
            @click="navigateToSource(s.source_id)"
          >
            <!-- Top Row: Icon, Name, Domain, Status -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <!-- Custom Monogram / Logo -->
                <div
                  v-if="s.source_name.toLowerCase().includes('smrikaam')"
                  class="flex size-10 items-center justify-center rounded-xl bg-purple-600 text-white shadow-sm"
                >
                  <!-- Stylized S monogram -->
                  <span class="text-lg font-black tracking-tighter">S</span>
                </div>
                <div
                  v-else-if="s.source_name.toLowerCase().includes('bitxhift')"
                  class="flex size-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm"
                >
                  <!-- Stylized X monogram -->
                  <span class="text-lg font-black tracking-tighter">X</span>
                </div>
                <div
                  v-else
                  class="flex size-10 items-center justify-center rounded-xl bg-gray-800 text-white shadow-sm"
                >
                  <span class="text-base font-bold">{{ s.source_name.charAt(0) }}</span>
                </div>

                <div>
                  <h3 class="text-base font-bold text-gray-900 dark:text-ink-white">
                    {{ s.source_name }}
                  </h3>
                  <p class="text-xs text-gray-500 dark:text-ink-gray-4">
                    @{{ s.domain }}
                  </p>
                </div>
              </div>

              <!-- Connection Status Pill -->
              <span
                class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
                :class="statusBadgeClass(s.connection_status)"
              >
                <span class="size-1.5 rounded-full" :class="statusDotClass(s.connection_status)"></span>
                {{ s.connection_status }}
              </span>
            </div>

            <!-- Bottom Row: Counts & Arrow -->
            <div class="mt-6 flex items-end justify-between border-t border-gray-50 pt-4 dark:border-surface-gray-7/60">
              <div class="flex items-center gap-8">
                <div>
                  <div class="text-xs text-gray-400 dark:text-ink-gray-4">{{ __('Total Bookings') }}</div>
                  <div class="text-xl font-bold text-gray-900 dark:text-ink-white">{{ s.total_bookings || 0 }}</div>
                </div>
                <div>
                  <div class="text-xs text-gray-400 dark:text-ink-gray-4">{{ __('New Bookings') }}</div>
                  <div class="text-xl font-bold text-gray-900 dark:text-ink-white">{{ s.new_bookings || 0 }}</div>
                </div>
              </div>

              <!-- Arrow Icon -->
              <div class="flex size-8 items-center justify-center rounded-full text-gray-400 transition group-hover:translate-x-1 group-hover:text-gray-900 dark:group-hover:text-ink-white">
                <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Recent Bookings Section -->
      <div class="rounded-2xl border border-gray-100 bg-white shadow-sm dark:border-surface-gray-7 dark:bg-surface-gray-8">
        <!-- Controls Bar -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 p-4 dark:border-surface-gray-7">
          <h2 class="text-base font-bold text-gray-900 dark:text-ink-white">
            {{ __('Recent Bookings') }}
          </h2>

          <div class="flex flex-wrap items-center gap-2.5">
            <!-- Source Filter Dropdown -->
            <select
              v-model="selectedSourceFilter"
              class="rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm focus:border-indigo-500 focus:outline-none dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
              @change="onFilterChange"
            >
              <option value="All">{{ __('All Sources') }}</option>
              <option v-for="s in sources" :key="s.source_id" :value="s.source_id">
                {{ s.source_name }}
              </option>
            </select>

            <!-- Search Input -->
            <div class="relative flex items-center">
              <span class="absolute left-3 text-gray-400">
                <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search bookings..."
                class="w-52 rounded-xl border border-gray-200 bg-white py-1.5 pl-8 pr-3 text-xs text-gray-900 placeholder-gray-400 shadow-sm focus:border-indigo-500 focus:outline-none dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white"
                @input="onSearch"
              />
            </div>

            <!-- View All Button -->
            <button
              type="button"
              class="rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 dark:border-surface-gray-6 dark:bg-surface-gray-9 dark:text-ink-white dark:hover:bg-surface-gray-7"
              @click="resetFilters"
            >
              {{ __('View All') }}
            </button>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-gray-100 bg-gray-50/50 text-[11px] font-bold uppercase tracking-wider text-gray-400 dark:border-surface-gray-7 dark:bg-surface-gray-9">
              <tr>
                <th class="py-3.5 pl-4 pr-2">
                  <input type="checkbox" class="rounded border-gray-300" />
                </th>
                <th class="px-3 py-3.5 font-bold">{{ __('CUSTOMER NAME') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('COMPANY') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('EMAIL') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('PHONE') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('SOURCE') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('APPOINTMENT DATE') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('TIME') }}</th>
                <th class="px-3 py-3.5 font-bold">{{ __('STATUS') }}</th>
                <th class="py-3.5 pl-3 pr-4 text-right font-bold">{{ __('ACTIONS') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-surface-gray-7">
              <tr
                v-for="b in bookings"
                :key="b.name"
                class="transition hover:bg-gray-50/60 dark:hover:bg-surface-gray-7/40"
              >
                <!-- Checkbox -->
                <td class="py-3.5 pl-4 pr-2">
                  <input type="checkbox" class="rounded border-gray-300" />
                </td>

                <!-- Customer Name -->
                <td class="px-3 py-3.5 font-semibold text-gray-900 dark:text-ink-white">
                  {{ b.customer_name }}
                </td>

                <!-- Company -->
                <td class="px-3 py-3.5 text-gray-600 dark:text-ink-gray-3">
                  {{ b.company_name || '—' }}
                </td>

                <!-- Email -->
                <td class="px-3 py-3.5 text-gray-600 dark:text-ink-gray-3">
                  {{ b.email }}
                </td>

                <!-- Phone -->
                <td class="px-3 py-3.5 text-gray-600 dark:text-ink-gray-3">
                  {{ b.phone || '—' }}
                </td>

                <!-- Source Badge -->
                <td class="px-3 py-3.5">
                  <span
                    class="inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold"
                    :class="sourceBadgeClass(b.source_name)"
                  >
                    {{ b.source_name || b.source }}
                  </span>
                </td>

                <!-- Appointment Date -->
                <td class="px-3 py-3.5 text-gray-700 dark:text-ink-gray-3">
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

                <!-- Appointment Time -->
                <td class="px-3 py-3.5 text-gray-700 dark:text-ink-gray-3">
                  <div class="flex items-center gap-1.5">
                    <svg class="size-3.5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    <span>{{ b.appointment_time || '—' }}</span>
                  </div>
                </td>

                <!-- Status Badge -->
                <td class="px-3 py-3.5">
                  <span
                    class="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold"
                    :class="bookingStatusBadgeClass(b.booking_status)"
                  >
                    {{ b.booking_status }}
                  </span>
                </td>

                <!-- Actions -->
                <td class="py-3.5 pl-3 pr-4 text-right">
                  <div class="flex items-center justify-end gap-1.5">
                    <!-- View Eye Icon -->
                    <button
                      type="button"
                      title="View Details"
                      class="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-surface-gray-7"
                      @click="openBookingDetail(b.name)"
                    >
                      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    </button>
                    <!-- Edit Pencil Icon -->
                    <button
                      type="button"
                      title="Manage Booking"
                      class="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-surface-gray-7"
                      @click="openBookingDetail(b.name)"
                    >
                      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9" />
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!bookings.length">
                <td colspan="10" class="py-12 text-center text-xs text-gray-400">
                  {{ __('No appointment bookings found matching current filters.') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Bottom Pagination Bar -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 p-4 dark:border-surface-gray-7">
          <!-- Page size toggle buttons -->
          <div class="flex items-center gap-1.5">
            <button
              v-for="size in [20, 50, 100]"
              :key="size"
              type="button"
              class="rounded-lg px-2.5 py-1 text-xs font-semibold transition"
              :class="pageSize === size ? 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300' : 'text-gray-500 hover:bg-gray-100 dark:text-ink-gray-4 dark:hover:bg-surface-gray-7'"
              @click="changePageSize(size)"
            >
              {{ size }}
            </button>
          </div>

          <!-- Total count and Load More -->
          <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-ink-gray-4">
            <span>{{ bookings.length }} of {{ totalBookingsCount }}</span>
            <button
              v-if="bookings.length < totalBookingsCount"
              type="button"
              class="font-semibold text-purple-700 hover:underline dark:text-purple-400"
              @click="loadMore"
            >
              {{ __('Load More') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AddSourceModal
      v-model="showAddSourceModal"
      @created="fetchData"
    />

    <BookingDetailModal
      v-model="showDetailModal"
      :bookingId="selectedBookingId"
      @updated="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import AddSourceModal from '@/components/Modals/AddSourceModal.vue'
import BookingDetailModal from '@/components/Modals/BookingDetailModal.vue'

const router = useRouter()

const loading = ref(false)
const showAddSourceModal = ref(false)
const showDetailModal = ref(false)
const selectedBookingId = ref('')

const metrics = reactive({
  total_bookings: 0,
  new_bookings: 0,
  upcoming_appointments: 0,
  completed_appointments: 0,
  cancelled_appointments: 0,
})

const sources = ref([])
const bookings = ref([])
const totalBookingsCount = ref(0)
const pageSize = ref(20)
const selectedSourceFilter = ref('All')
const searchQuery = ref('')

onMounted(() => {
  fetchData()
})

async function fetchData() {
  loading.value = true
  try {
    await Promise.all([fetchSummary(), fetchBookings()])
  } finally {
    loading.value = false
  }
}

async function fetchSummary() {
  try {
    const res = await call('crm.api.booking_hub.get_booking_hub_summary')
    if (res && res.metrics) {
      metrics.total_bookings = res.metrics.total_bookings || 0
      metrics.new_bookings = res.metrics.new_bookings || 0
      metrics.upcoming_appointments = res.metrics.upcoming_appointments || 0
      metrics.completed_appointments = res.metrics.completed_appointments || 0
      metrics.cancelled_appointments = res.metrics.cancelled_appointments || 0
      sources.value = res.sources || []
    }
  } catch (err) {
    console.error('Error fetching summary:', err)
  }
}

async function fetchBookings() {
  try {
    const res = await call('crm.api.booking_hub.get_bookings', {
      source_id: selectedSourceFilter.value === 'All' ? '' : selectedSourceFilter.value,
      status: 'All',
      search: searchQuery.value,
      page_length: pageSize.value,
      start: 0,
    })
    if (res) {
      bookings.value = res.bookings || []
      totalBookingsCount.value = res.total_count || 0
    }
  } catch (err) {
    console.error('Error fetching bookings:', err)
  }
}

async function loadMore() {
  try {
    const res = await call('crm.api.booking_hub.get_bookings', {
      source_id: selectedSourceFilter.value === 'All' ? '' : selectedSourceFilter.value,
      status: 'All',
      search: searchQuery.value,
      page_length: pageSize.value,
      start: bookings.value.length,
    })
    if (res && res.bookings) {
      bookings.value = [...bookings.value, ...res.bookings]
      totalBookingsCount.value = res.total_count || 0
    }
  } catch (err) {
    console.error('Error loading more bookings:', err)
  }
}

let searchDebounce = null
function onSearch() {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    fetchBookings()
  }, 300)
}

function onFilterChange() {
  fetchBookings()
}

function resetFilters() {
  selectedSourceFilter.value = 'All'
  searchQuery.value = ''
  fetchBookings()
}

function changePageSize(size) {
  pageSize.value = size
  fetchBookings()
}

function navigateToSource(sourceId) {
  router.push(`/booking-hub/source/${sourceId}`)
}

function openBookingDetail(id) {
  selectedBookingId.value = id
  showDetailModal.value = true
}

function sourceBadgeClass(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('smrikaam')) {
    return 'bg-purple-50 text-purple-700 border border-purple-100 dark:bg-purple-950 dark:text-purple-300'
  }
  if (n.includes('bitxhift')) {
    return 'bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950 dark:text-blue-300'
  }
  return 'bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-800 dark:text-gray-300'
}

function statusBadgeClass(status) {
  switch (status) {
    case 'Connected':
      return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
    case 'Testing':
      return 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
    case 'Connection Failed':
      return 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
    case 'Inactive':
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
    default:
      return 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
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
    case 'Inactive':
      return 'bg-gray-400'
    default:
      return 'bg-amber-500'
  }
}

function bookingStatusBadgeClass(status) {
  switch (status) {
    case 'New':
      return 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300'
    case 'Upcoming':
      return 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300'
    case 'Confirmed':
      return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
    case 'Completed':
      return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
    case 'Cancelled':
      return 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
    case 'Rescheduled':
      return 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  }
}
</script>
