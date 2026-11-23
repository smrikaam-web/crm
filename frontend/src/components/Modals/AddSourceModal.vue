<template>
  <Dialog v-model:open="isOpen" bare>
    <template #default>
      <div class="relative w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-surface-gray-9 dark:text-ink-white">
        <!-- Close button top right -->
        <button
          type="button"
          class="absolute right-4 top-4 z-10 flex size-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-surface-gray-8 dark:hover:text-ink-white"
          @click="closeModal"
        >
          <span class="text-xl leading-none">&times;</span>
        </button>

        <!-- STEP 1: CREATE SOURCE FORM -->
        <div v-if="step === 'form'" class="p-6">
          <!-- Modal Header -->
          <div class="flex items-start gap-3.5 mb-6">
            <div class="flex size-10 items-center justify-center rounded-full bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400">
              <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="2" y1="12" x2="22" y2="12" />
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-bold text-gray-900 dark:text-ink-white">
                {{ __('Connect Website Source') }}
              </h2>
              <p class="text-xs text-gray-500 dark:text-ink-gray-5">
                {{ __('Configure your website appointment integration') }}
              </p>
            </div>
          </div>

          <!-- Error Alert -->
          <div
            v-if="errorMessage"
            class="mb-4 rounded-lg bg-red-50 p-3 text-xs text-red-700 dark:bg-red-950/50 dark:text-red-400"
          >
            {{ errorMessage }}
          </div>

          <!-- Form Fields -->
          <div class="space-y-4">
            <!-- Source Name -->
            <div>
              <label class="mb-1 block text-xs font-semibold text-gray-700 dark:text-ink-gray-3">
                {{ __('Source Name') }} <span class="text-red-500">*</span>
              </label>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-gray-400">
                  <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7" />
                    <rect x="14" y="3" width="7" height="7" />
                    <rect x="14" y="14" width="7" height="7" />
                    <rect x="3" y="14" width="7" height="7" />
                  </svg>
                </span>
                <input
                  v-model="form.source_name"
                  type="text"
                  placeholder="Enter source name (e.g., Smrikaam Corporate)"
                  class="w-full rounded-xl border border-gray-200 bg-gray-50/50 py-2.5 pl-9 pr-3 text-sm text-gray-900 placeholder-gray-400 transition focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
                />
              </div>
            </div>

            <!-- Website Domain -->
            <div>
              <label class="mb-1 block text-xs font-semibold text-gray-700 dark:text-ink-gray-3">
                {{ __('Website Domain') }} <span class="text-red-500">*</span>
              </label>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-gray-400">
                  <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                </span>
                <input
                  v-model="form.domain"
                  type="text"
                  placeholder="example.com (no http:// or /path)"
                  class="w-full rounded-xl border border-gray-200 bg-gray-50/50 py-2.5 pl-9 pr-3 text-sm text-gray-900 placeholder-gray-400 transition focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
                />
              </div>
            </div>

            <!-- Website Type -->
            <div>
              <label class="mb-1 block text-xs font-semibold text-gray-700 dark:text-ink-gray-3">
                {{ __('Website Type') }} <span class="text-red-500">*</span>
              </label>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-gray-400">
                  <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                    <line x1="8" y1="21" x2="16" y2="21" />
                    <line x1="12" y1="17" x2="12" y2="21" />
                  </svg>
                </span>
                <select
                  v-model="form.website_type"
                  class="w-full rounded-xl border border-gray-200 bg-gray-50/50 py-2.5 pl-9 pr-8 text-sm text-gray-900 transition focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
                >
                  <option value="Corporate">{{ __('Corporate Website') }}</option>
                  <option value="Product">{{ __('Product Website') }}</option>
                  <option value="Other">{{ __('Other') }}</option>
                </select>
              </div>
            </div>

            <!-- Description -->
            <div>
              <label class="mb-1 block text-xs font-semibold text-gray-700 dark:text-ink-gray-3">
                {{ __('Description') }} <span class="text-gray-400">({{ __('Optional') }})</span>
              </label>
              <textarea
                v-model="form.description"
                rows="2"
                placeholder="Brief notes about this website source..."
                class="w-full rounded-xl border border-gray-200 bg-gray-50/50 p-2.5 text-sm text-gray-900 placeholder-gray-400 transition focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-white"
              ></textarea>
            </div>

            <!-- Form Settings: Form Active Toggle -->
            <div>
              <span class="mb-1.5 block text-xs font-semibold text-gray-500 dark:text-ink-gray-4">
                {{ __('Form Settings') }}
              </span>
              <div class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-3.5 dark:border-surface-gray-7 dark:bg-surface-gray-8">
                <div class="flex items-center gap-3">
                  <div
                    class="flex size-9 items-center justify-center rounded-lg transition-colors"
                    :class="form.is_active ? 'bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400' : 'bg-gray-100 text-gray-400 dark:bg-surface-gray-7 dark:text-ink-gray-5'"
                  >
                    <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 20h9" />
                      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                    </svg>
                  </div>
                  <div>
                    <div class="text-xs font-bold text-gray-900 dark:text-ink-white">
                      {{ __('Form Active') }}
                    </div>
                    <div class="text-[11px] text-gray-500 dark:text-ink-gray-5">
                      {{ __('Visitors can fill out the form and submit appointment bookings') }}
                    </div>
                  </div>
                </div>

                <!-- Toggle Switch with Explicit Status Label -->
                <div class="flex items-center gap-2.5">
                  <span
                    class="select-none text-xs font-bold transition-colors"
                    :class="form.is_active ? 'text-purple-600 dark:text-purple-400' : 'text-gray-400 dark:text-ink-gray-5'"
                  >
                    {{ form.is_active ? __('Active') : __('Inactive') }}
                  </span>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="form.is_active"
                    class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border border-black/5 p-0.5 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1"
                    :class="form.is_active ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-700'"
                    @click="form.is_active = !form.is_active"
                  >
                    <span
                      class="pointer-events-none inline-block size-5 transform rounded-full bg-white border border-black/10 shadow-sm transition duration-200 ease-in-out"
                      :class="form.is_active ? 'translate-x-5' : 'translate-x-0'"
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="mt-6 flex items-center justify-end gap-3 border-t border-gray-100 pt-4 dark:border-surface-gray-8">
            <button
              type="button"
              class="rounded-xl border border-gray-200 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 dark:border-surface-gray-7 dark:text-ink-gray-3 dark:hover:bg-surface-gray-8"
              @click="closeModal"
            >
              {{ __('Cancel') }}
            </button>
            <button
              type="button"
              :disabled="saving || !form.source_name?.trim() || !form.domain?.trim()"
              class="flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-xs font-bold text-gray-900 shadow-sm transition-all hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white disabled:hover:border-gray-300 dark:border-surface-gray-6 dark:bg-surface-gray-8 dark:text-ink-white dark:hover:bg-surface-gray-7"
              @click="handleCreateSource"
            >
              <svg v-if="saving" class="size-3.5 animate-spin text-gray-900 dark:text-ink-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25" />
                <path d="M4 12a8 8 0 018-8v8H4z" class="opacity-75" fill="currentColor" />
              </svg>
              <span>{{ saving ? __('Creating...') : __('Create Source') }}</span>
            </button>
          </div>
        </div>

        <!-- STEP 2: INTEGRATION SETUP SCREEN -->
        <div v-else-if="step === 'setup'" class="max-h-[85vh] overflow-y-auto p-6">
          <!-- Setup Header -->
          <div class="mb-4 flex items-center justify-between border-b border-gray-100 pb-3 dark:border-surface-gray-8">
            <div class="flex items-center gap-2.5">
              <div class="flex size-9 items-center justify-center rounded-xl bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400">
                <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-bold text-gray-900 dark:text-ink-white">
                  {{ __('Integration Setup') }}
                </h3>
                <p class="text-xs text-gray-500">
                  {{ createdSource.source_name }} ({{ createdSource.domain }})
                </p>
              </div>
            </div>
            <span
              class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
              :class="statusBadgeClass(createdSource.connection_status)"
            >
              <span class="size-1.5 rounded-full" :class="statusDotClass(createdSource.connection_status)"></span>
              {{ createdSource.connection_status }}
            </span>
          </div>

          <!-- Secret Warning Box -->
          <div class="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300">
            <div class="flex items-start gap-2">
              <span class="text-sm">⚠️</span>
              <div>
                <strong class="font-semibold">{{ __('Copy your API Secret now!') }}</strong>
                <p class="mt-0.5 text-[11px] leading-relaxed">
                  {{ __('For maximum security, the API Secret is generated once and will never be displayed again. Store it securely in your server-side environment.') }}
                </p>
              </div>
            </div>
          </div>

          <!-- Credentials Grid -->
          <div class="space-y-3">
            <!-- Source Identifier -->
            <div>
              <label class="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {{ __('Source Identifier') }}
              </label>
              <div class="mt-1 flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-xs text-gray-800 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2">
                <span>{{ createdSource.source_id }}</span>
                <button
                  type="button"
                  class="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  @click="copyText(createdSource.source_id, 'source_id')"
                >
                  {{ copiedField === 'source_id' ? __('Copied!') : __('Copy') }}
                </button>
              </div>
            </div>

            <!-- API Endpoint -->
            <div>
              <label class="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {{ __('API Endpoint (POST)') }}
              </label>
              <div class="mt-1 flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-xs text-gray-800 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2">
                <span class="truncate pr-2">{{ apiEndpoint }}</span>
                <button
                  type="button"
                  class="shrink-0 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  @click="copyText(apiEndpoint, 'endpoint')"
                >
                  {{ copiedField === 'endpoint' ? __('Copied!') : __('Copy') }}
                </button>
              </div>
            </div>

            <!-- API Key -->
            <div>
              <label class="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {{ __('API Key (X-CRM-Source-Key)') }}
              </label>
              <div class="mt-1 flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-xs text-gray-800 dark:border-surface-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2">
                <span class="truncate pr-2">{{ createdSource.api_key }}</span>
                <button
                  type="button"
                  class="shrink-0 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  @click="copyText(createdSource.api_key, 'key')"
                >
                  {{ copiedField === 'key' ? __('Copied!') : __('Copy') }}
                </button>
              </div>
            </div>

            <!-- API Secret (One-time) -->
            <div>
              <label class="text-[11px] font-semibold uppercase tracking-wider text-amber-600">
                {{ __('API Secret (X-CRM-Source-Secret) – One-Time View') }}
              </label>
              <div class="mt-1 flex items-center justify-between rounded-lg border border-amber-300 bg-amber-50/60 px-3 py-2 font-mono text-xs text-gray-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-ink-white">
                <span class="break-all pr-2 font-bold">{{ createdSource.api_secret }}</span>
                <button
                  type="button"
                  class="shrink-0 text-xs font-bold text-amber-700 hover:text-amber-900 dark:text-amber-400"
                  @click="copyText(createdSource.api_secret, 'secret')"
                >
                  {{ copiedField === 'secret' ? __('Copied!') : __('Copy') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Sample JSON Payload & cURL -->
          <div class="mt-4">
            <div class="mb-1 flex items-center justify-between">
              <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {{ __('Sample Request Body (JSON)') }}
              </span>
              <button
                type="button"
                class="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                @click="copyText(samplePayload, 'payload')"
              >
                {{ copiedField === 'payload' ? __('Copied!') : __('Copy JSON') }}
              </button>
            </div>
            <pre class="overflow-x-auto rounded-lg bg-gray-900 p-3 text-[11px] font-mono leading-relaxed text-gray-100">{{ samplePayload }}</pre>
          </div>

          <!-- Test Connection & Status result -->
          <div class="mt-4 rounded-xl border border-gray-200 bg-gray-50/70 p-3.5 dark:border-surface-gray-7 dark:bg-surface-gray-8">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-gray-900 dark:text-ink-white">
                  {{ __('Test Connection') }}
                </div>
                <div class="text-[11px] text-gray-500">
                  {{ __('Simulate a ping to verify website credentials and activate connection') }}
                </div>
              </div>
              <button
                type="button"
                :disabled="testingConnection"
                class="flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50 dark:border-surface-gray-6 dark:bg-surface-gray-7 dark:text-ink-white"
                @click="runTestConnection"
              >
                <svg v-if="testingConnection" class="size-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="12" r="10" stroke-width="4" class="opacity-25" />
                  <path d="M4 12a8 8 0 018-8v8H4z" class="opacity-75" fill="currentColor" />
                </svg>
                <span>{{ testingConnection ? __('Testing...') : __('Test Connection') }}</span>
              </button>
            </div>
            <div v-if="testResult" class="mt-2 text-xs font-semibold" :class="testResult.success ? 'text-green-600' : 'text-red-600'">
              {{ testResult.message }}
            </div>
          </div>

          <!-- Done button -->
          <div class="mt-6 flex items-center justify-end border-t border-gray-100 pt-4 dark:border-surface-gray-8">
            <button
              type="button"
              class="rounded-xl bg-gray-900 px-6 py-2 text-xs font-bold text-white hover:bg-black"
              @click="finishSetup"
            >
              {{ __('Done / Finish Setup') }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { call, Dialog } from 'frappe-ui'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const step = ref('form')
const saving = ref(false)
const errorMessage = ref('')
const testingConnection = ref(false)
const testResult = ref(null)
const copiedField = ref('')

const form = reactive({
  source_name: '',
  domain: '',
  website_type: 'Corporate',
  description: '',
  is_active: true,
})

const createdSource = reactive({
  source_id: '',
  source_name: '',
  domain: '',
  connection_status: 'Pending Setup',
  api_key: '',
  api_secret: '',
})

const apiEndpoint = computed(() => {
  const origin = window.location.origin
  return `${origin}/api/method/crm.api.booking_hub.create_booking`
})

const samplePayload = computed(() => {
  return JSON.stringify(
    {
      source_id: createdSource.source_id || 'src_mywebsite',
      customer_name: 'John Doe',
      company_name: 'Acme Corporation',
      email: 'john@example.com',
      phone: '+1 555-0199',
      interested_service: 'Technical Staffing / AI Engineering',
      appointment_date: '2026-12-01',
      appointment_time: '10:00 AM',
      timezone: 'Asia/Kolkata',
      message: 'Looking to hire 3 senior full-stack engineers.',
      page_url: `https://${createdSource.domain || 'example.com'}/schedule-call`,
    },
    null,
    2
  )
})

function closeModal() {
  isOpen.value = false
  setTimeout(() => {
    step.value = 'form'
    errorMessage.value = ''
    testResult.value = null
    form.source_name = ''
    form.domain = ''
    form.description = ''
    form.is_active = true
  }, 200)
}

function finishSetup() {
  emit('created')
  closeModal()
}

async function handleCreateSource() {
  if (saving.value) return
  errorMessage.value = ''
  if (!form.source_name?.trim()) {
    errorMessage.value = 'Source Name is mandatory.'
    return
  }
  if (!form.domain?.trim()) {
    errorMessage.value = 'Website Domain is mandatory.'
    return
  }

  saving.value = true
  try {
    const res = await call('crm.api.booking_hub.add_source', {
      source_name: form.source_name.trim(),
      domain: form.domain.trim(),
      website_type: form.website_type || 'Corporate',
      description: form.description?.trim() || '',
      is_active: form.is_active ? 1 : 0,
    })

    const src = res?.source || res
    if (src && src.source_id) {
      createdSource.source_id = src.source_id
      createdSource.source_name = src.source_name
      createdSource.domain = src.domain
      createdSource.connection_status = src.connection_status || 'Pending Setup'
      createdSource.api_key = src.api_key
      createdSource.api_secret = src.api_secret
      step.value = 'setup'
    } else {
      errorMessage.value = res?.message || 'Failed to create source. Please verify fields and try again.'
    }
  } catch (err) {
    let msg = err.message || ''
    if (err.messages && err.messages.length) {
      msg = err.messages.join(' ')
    } else if (err._server_messages) {
      try {
        const parsed = JSON.parse(err._server_messages)
        msg = parsed.map((m) => {
          try {
            return JSON.parse(m).message
          } catch {
            return m
          }
        }).join(' ')
      } catch {
        msg = err._server_messages
      }
    }
    errorMessage.value = msg || 'An error occurred while creating the source.'
  } finally {
    saving.value = false
  }
}

async function runTestConnection() {
  if (!createdSource.source_id) return
  testingConnection.value = true
  testResult.value = null
  try {
    const res = await call('crm.api.booking_hub.test_connection', {
      source_id: createdSource.source_id,
    })
    if (res && res.status === 'success') {
      testResult.value = { success: true, message: '✓ ' + res.message }
      createdSource.connection_status = 'Connected'
    } else {
      testResult.value = { success: false, message: '✗ ' + (res?.message || 'Connection test failed.') }
    }
  } catch (err) {
    testResult.value = { success: false, message: '✗ ' + (err.message || 'Connection test error.') }
  } finally {
    testingConnection.value = false
  }
}

function copyText(val, key) {
  if (!val) return
  navigator.clipboard.writeText(val)
  copiedField.value = key
  setTimeout(() => {
    if (copiedField.value === key) copiedField.value = ''
  }, 2000)
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
