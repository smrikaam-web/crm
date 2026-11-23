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
          <h1 class="text-lg font-bold text-ink-gray-9 dark:text-ink-white">
            {{ __('Manage Website Sources') }}
          </h1>
          <p class="text-xs text-ink-gray-5">
            {{ __('Configure website connections, security credentials, and integration settings') }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-xl bg-gray-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-black"
          @click="showAddSourceModal = true"
        >
          <span>+ {{ __('Add Source') }}</span>
        </button>
        <button
          type="button"
          class="flex size-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 shadow-sm hover:bg-gray-50 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
          @click="fetchSources"
        >
          <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Content -->
    <div class="p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <svg class="size-8 animate-spin text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25" />
          <path d="M4 12a8 8 0 018-8v8H4z" class="opacity-75" fill="currentColor" />
        </svg>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="s in sources"
          :key="s.source_id"
          class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow dark:border-surface-gray-7 dark:bg-surface-gray-8"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <!-- Left: Logo & Info -->
            <div class="flex items-start gap-3.5">
              <div
                class="flex size-11 items-center justify-center rounded-2xl font-black text-white"
                :class="s.source_name.toLowerCase().includes('smrikaam') ? 'bg-gradient-to-br from-purple-500 to-indigo-600' : 'bg-gradient-to-br from-blue-500 to-sky-600'"
              >
                {{ s.source_name.charAt(0) }}
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="text-base font-bold text-gray-900 dark:text-ink-white">
                    {{ s.source_name }}
                  </h3>
                  <span
                    class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                    :class="statusBadgeClass(s.connection_status)"
                  >
                    <span class="size-1.5 rounded-full" :class="statusDotClass(s.connection_status)"></span>
                    {{ s.connection_status }}
                  </span>
                </div>
                <div class="mt-0.5 text-xs text-gray-500">
                  <span class="font-medium text-gray-700 dark:text-ink-gray-3">@{{ s.domain }}</span>
                  <span class="mx-1.5">•</span>
                  <span>{{ s.source_id }}</span>
                  <span class="mx-1.5">•</span>
                  <span>{{ s.website_type || 'Website Source' }}</span>
                </div>
                <div v-if="s.description" class="mt-1 text-xs text-gray-500">
                  {{ s.description }}
                </div>
              </div>
            </div>

            <!-- Right: Status Toggle & Bookings Count -->
            <div class="flex items-center gap-4">
              <div class="text-right">
                <div class="text-xs text-gray-400">{{ __('Total Bookings') }}</div>
                <div class="text-lg font-bold text-gray-900 dark:text-ink-white">{{ s.total_bookings || 0 }}</div>
              </div>

              <!-- Active Toggle -->
              <div class="flex items-center gap-2 border-l border-gray-100 pl-4 dark:border-surface-gray-7">
                <span class="text-xs font-medium text-gray-500">{{ s.is_active ? __('Active') : __('Disabled') }}</span>
                <button
                  type="button"
                  class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                  :class="s.is_active ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'"
                  @click="toggleActive(s)"
                >
                  <span
                    class="pointer-events-none inline-block size-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                    :class="s.is_active ? 'translate-x-4' : 'translate-x-0'"
                  />
                </button>
              </div>
            </div>
          </div>

          <!-- Bottom Meta & Actions -->
          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-3 text-xs text-gray-500 dark:border-surface-gray-7 dark:text-ink-gray-4">
            <div class="flex items-center gap-4">
              <span>{{ __('Credentials:') }} <code class="font-mono text-gray-700 dark:text-ink-gray-2">{{ s.credential_reference || 'Configured' }}</code></span>
              <span>{{ __('Last Booking:') }} <span class="font-medium text-gray-700 dark:text-ink-gray-2">{{ s.last_successful_booking || 'None' }}</span></span>
            </div>

            <div class="flex items-center gap-2">
              <button
                type="button"
                class="rounded-lg border border-gray-200 px-3 py-1 font-semibold text-gray-700 hover:bg-gray-50 dark:border-surface-gray-6 dark:text-ink-white"
                @click="testConnection(s.source_id)"
              >
                {{ __('Test Connection') }}
              </button>
              <button
                type="button"
                class="rounded-lg border border-amber-200 px-3 py-1 font-semibold text-amber-700 hover:bg-amber-50 dark:border-amber-900/60 dark:text-amber-400"
                @click="regenerateSecret(s.source_id)"
              >
                {{ __('Regenerate Secret') }}
              </button>
              <router-link
                :to="'/booking-hub/source/' + s.source_id"
                class="rounded-lg bg-indigo-50 px-3 py-1 font-semibold text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950 dark:text-indigo-300"
              >
                {{ __('View Bookings →') }}
              </router-link>
            </div>
          </div>
        </div>

        <div v-if="!sources.length" class="rounded-2xl border border-gray-200 p-12 text-center text-gray-400">
          {{ __('No website sources registered yet.') }}
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AddSourceModal
      v-model="showAddSourceModal"
      @created="fetchSources"
    />

    <!-- Regenerated Secret Modal -->
    <Dialog v-model:open="showSecretModal" bare>
      <template #default>
        <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-surface-gray-9 dark:text-ink-white">
          <div class="mb-4 flex items-center gap-2.5 text-amber-600">
            <span class="text-xl">⚠️</span>
            <h3 class="text-base font-bold text-gray-900 dark:text-ink-white">{{ __('New API Secret Generated') }}</h3>
          </div>
          <p class="text-xs text-gray-600 dark:text-ink-gray-4">
            {{ __('Please copy and store your new API secret securely. The previous secret has been invalidated.') }}
          </p>
          <div class="mt-3 rounded-xl border border-amber-300 bg-amber-50/70 p-3 font-mono text-xs font-bold break-all text-gray-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-ink-white">
            {{ newlyGeneratedSecret }}
          </div>
          <div class="mt-5 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-lg bg-gray-900 px-4 py-2 text-xs font-semibold text-white hover:bg-black"
              @click="showSecretModal = false"
            >
              {{ __('I have stored this secret') }}
            </button>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call, Dialog } from 'frappe-ui'
import AddSourceModal from '@/components/Modals/AddSourceModal.vue'

const loading = ref(false)
const sources = ref([])
const showAddSourceModal = ref(false)
const showSecretModal = ref(false)
const newlyGeneratedSecret = ref('')

onMounted(() => {
  fetchSources()
})

async function fetchSources() {
  loading.value = true
  try {
    const res = await call('crm.api.booking_hub.get_booking_hub_summary')
    if (res && res.sources) {
      sources.value = res.sources || []
    }
  } catch (err) {
    console.error('Error fetching sources:', err)
  } finally {
    loading.value = false
  }
}

async function testConnection(sourceId) {
  try {
    const res = await call('crm.api.booking_hub.test_connection', {
      source_id: sourceId,
    })
    alert(res.message || 'Connection test completed')
    fetchSources()
  } catch (err) {
    alert('Connection test failed: ' + err.message)
  }
}

async function regenerateSecret(sourceId) {
  if (!confirm('Are you sure you want to regenerate credentials for ' + sourceId + '? Any existing website webhook will fail until updated.')) {
    return
  }
  try {
    const res = await call('crm.api.booking_hub.regenerate_credentials', {
      source_id: sourceId,
    })
    if (res && res.api_secret) {
      newlyGeneratedSecret.value = res.api_secret
      showSecretModal.value = true
      fetchSources()
    }
  } catch (err) {
    alert('Failed to regenerate: ' + err.message)
  }
}

async function toggleActive(source) {
  const newStatus = !source.is_active
  try {
    await call('crm.api.booking_hub.toggle_source_status', {
      source_id: source.source_id,
      is_active: newStatus ? 1 : 0,
    })
    source.is_active = newStatus
    source.connection_status = newStatus ? 'Connected' : 'Inactive'
  } catch (err) {
    alert('Failed to update status: ' + err.message)
  }
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
</script>
