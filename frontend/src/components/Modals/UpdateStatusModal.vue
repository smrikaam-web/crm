<template>
  <Dialog
    v-model:open="show"
    size="lg"
  >
    <template #title>
      <div class="flex flex-col">
        <div class="text-lg font-semibold text-ink-gray-9">{{ __('Update Status') }}</div>
        <div v-if="contactName" class="text-xs font-normal text-ink-gray-6 mt-0.5">
          {{ contactName }}
        </div>
      </div>
    </template>

    <template #default>
      <form class="space-y-4 py-1" @submit.prevent="submitForm">
        <!-- Error Banner if any -->
        <div
          v-if="errorMessage"
          class="rounded-md bg-surface-red-2 p-2.5 text-xs font-medium text-ink-red-4 border border-outline-red-2"
        >
          {{ errorMessage }}
        </div>

        <!-- 1. Main Status (Required) -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
            {{ __('Main Status') }} <span class="text-ink-red-3">*</span>
          </label>
          <select
            v-model="form.main_status"
            class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none transition-colors"
            required
            @change="onMainStatusChange"
          >
            <option value="Contacted">{{ __('Contacted') }}</option>
            <option value="Not Contacted">{{ __('Not Contacted') }}</option>
            <option value="Not Valid">{{ __('Not Valid') }}</option>
          </select>
        </div>

        <!-- 2. Connected to -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
            {{ __('Connected to') }}
          </label>
          <input
            v-model="form.connected_to"
            type="text"
            class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none transition-colors"
            placeholder="Decision Maker (already confirmed)"
          />
        </div>

        <!-- 3. Activity Status (Only visible when Main Status = Contacted) -->
        <div v-if="form.main_status === 'Contacted'" class="space-y-4">
          <div>
            <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
              {{ __('Activity Status') }} <span class="text-ink-red-3">*</span>
            </label>
            <select
              v-model="form.activity_status"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none transition-colors"
              required
              @change="onActivityStatusChange"
            >
              <option value="Portfolio Sent">{{ __('Portfolio Sent') }}</option>
              <option value="Requirement Gathered">{{ __('Requirement Gathered') }}</option>
              <option value="Call Back">{{ __('Call Back') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
              <option value="Follow Up">{{ __('Follow Up') }}</option>
            </select>
          </div>

          <!-- A. Portfolio Sent Subfields -->
          <div v-if="form.activity_status === 'Portfolio Sent'" class="space-y-3.5 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3.5">
            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Next Follow-up Date') }} <span class="text-ink-red-3">*</span>
              </label>
              <input
                v-model="form.follow_up_date"
                type="date"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                required
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Next Action') }}
              </label>
              <!-- Quick Select Chips -->
              <div class="flex flex-wrap gap-1.5 mb-2">
                <button
                  v-for="chip in portfolioChips"
                  :key="chip"
                  type="button"
                  class="rounded-full px-2.5 py-1 text-xs font-medium transition-colors border"
                  :class="form.next_action === chip ? 'bg-surface-gray-9 text-surface-white border-surface-gray-9' : 'bg-surface-white text-ink-gray-7 border-outline-gray-2 hover:bg-surface-gray-2'"
                  @click="form.next_action = chip"
                >
                  {{ chip }}
                </button>
              </div>
              <input
                v-model="form.next_action"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                placeholder="e.g. Send portfolio"
              />
            </div>
          </div>

          <!-- B. Requirement Gathered Subfields -->
          <div v-else-if="form.activity_status === 'Requirement Gathered'" class="space-y-3.5 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3.5">
            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Next Follow-up Date') }} <span class="text-ink-red-3">*</span>
              </label>
              <input
                v-model="form.follow_up_date"
                type="date"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                required
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Next Action') }}
              </label>
              <!-- Quick Select Chips -->
              <div class="flex flex-wrap gap-1.5 mb-2">
                <button
                  v-for="chip in requirementChips"
                  :key="chip"
                  type="button"
                  class="rounded-full px-2.5 py-1 text-xs font-medium transition-colors border"
                  :class="form.next_action === chip ? 'bg-surface-gray-9 text-surface-white border-surface-gray-9' : 'bg-surface-white text-ink-gray-7 border-outline-gray-2 hover:bg-surface-gray-2'"
                  @click="form.next_action = chip"
                >
                  {{ chip }}
                </button>
              </div>
              <input
                v-model="form.next_action"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                placeholder="e.g. Book discovery call"
              />
            </div>
          </div>

          <!-- C. Call Back Subfield -->
          <div v-else-if="form.activity_status === 'Call Back'" class="space-y-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3.5">
            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Next Call On') }} <span class="text-ink-red-3">*</span>
              </label>
              <input
                v-model="form.call_back_date"
                type="date"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                required
              />
            </div>
          </div>

          <!-- D. Follow Up Subfield -->
          <div v-else-if="form.activity_status === 'Follow Up'" class="space-y-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3.5">
            <div>
              <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">
                {{ __('Follow Up Date') }} <span class="text-ink-red-3">*</span>
              </label>
              <input
                v-model="form.follow_up_date"
                type="date"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
                required
              />
            </div>
          </div>
        </div>

        <!-- 4. Description (Required, Min 15 Characters) -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-medium text-ink-gray-7">
              {{ __('Description') }} <span class="text-ink-red-3">*</span>
            </label>
            <span
              class="text-xs font-mono font-medium transition-colors"
              :class="charCount >= 15 ? 'text-ink-green-3' : (form.description.length > 0 ? 'text-ink-red-3' : 'text-ink-gray-5')"
            >
              {{ charCount }} / 15
            </span>
          </div>
          <textarea
            v-model="form.description"
            rows="4"
            class="w-full rounded-md border bg-surface-white p-3 text-sm text-ink-gray-9 focus:outline-none transition-colors"
            :class="[
              charCount >= 15
                ? 'border-outline-gray-2 focus:border-outline-gray-4'
                : (form.description.length > 0 || submitted
                    ? 'border-outline-red-3 focus:border-outline-red-4'
                    : 'border-outline-gray-2 focus:border-outline-gray-4'),
            ]"
            :placeholder="__('Enter status details and notes (minimum 15 characters required)...')"
            required
          />
          <div class="flex items-center justify-between text-[11px] mt-1 text-ink-gray-5">
            <span v-if="charCount < 15 && form.description.length > 0" class="text-ink-red-3">
              {{ __('Minimum 15 characters required ({0} more needed)', [15 - charCount]) }}
            </span>
            <span v-else-if="charCount >= 15" class="text-ink-green-3">
              {{ __('Character requirement met.') }}
            </span>
            <span v-else>
              {{ __('At least 15 characters are required to submit.') }}
            </span>
          </div>
        </div>
      </form>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button
          variant="subtle"
          :label="__('Cancel')"
          :disabled="saving"
          @click="show = false"
        />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          :disabled="saving || charCount < 15"
          @click="submitForm"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, toast, call } from 'frappe-ui'
import { ref, reactive, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  contact: { type: Object, default: () => ({}) },
  contactId: { type: String, required: true },
  taskId: { type: [String, Number], default: null },
})

const emit = defineEmits(['update:modelValue', 'updated'])

const show = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const contactName = computed(() => {
  return props.contact?.full_name || props.contactId
})

const portfolioChips = ['Send portfolio', 'Share case studies', 'Schedule discovery call']
const requirementChips = ['Book discovery call', 'Send proposal', 'Confirm requirements']

const form = reactive({
  main_status: 'Contacted',
  connected_to: 'Decision Maker (already confirmed)',
  activity_status: 'Portfolio Sent',
  next_action: '',
  follow_up_date: '',
  call_back_date: '',
  description: '',
})

const charCount = computed(() => {
  return (form.description || '').trim().length
})

const saving = ref(false)
const submitted = ref(false)
const errorMessage = ref('')

function onMainStatusChange() {
  if (form.main_status !== 'Contacted') {
    form.activity_status = ''
    form.next_action = ''
    form.follow_up_date = ''
    form.call_back_date = ''
  } else if (!form.activity_status) {
    form.activity_status = 'Portfolio Sent'
  }
}

function onActivityStatusChange() {
  form.next_action = ''
  form.follow_up_date = ''
  form.call_back_date = ''
}

// Reset form when modal opens
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      submitted.value = false
      errorMessage.value = ''
      form.main_status = 'Contacted'
      form.connected_to = 'Decision Maker (already confirmed)'
      form.activity_status = 'Portfolio Sent'
      form.next_action = ''
      form.follow_up_date = ''
      form.call_back_date = ''
      form.description = ''
    }
  },
)

async function submitForm() {
  submitted.value = true
  errorMessage.value = ''

  if (charCount.value < 15) {
    errorMessage.value = __('Description must be at least 15 characters long.')
    return
  }

  if (form.main_status === 'Contacted') {
    if (
      ['Portfolio Sent', 'Requirement Gathered', 'Follow Up'].includes(
        form.activity_status,
      ) &&
      !form.follow_up_date
    ) {
      errorMessage.value = __('Please select a follow-up date.')
      return
    }
    if (form.activity_status === 'Call Back' && !form.call_back_date) {
      errorMessage.value = __('Please select next call date.')
      return
    }
  }

  saving.value = true
  try {
    const res = await call('crm.api.contact.create_prospect_status_update', {
      contact: props.contactId,
      main_status: form.main_status,
      connected_to: form.connected_to || 'Decision Maker (already confirmed)',
      activity_status:
        form.main_status === 'Contacted' ? form.activity_status : null,
      next_action:
        form.main_status === 'Contacted' ? form.next_action || null : null,
      follow_up_date:
        form.main_status === 'Contacted' ? form.follow_up_date || null : null,
      call_back_date:
        form.main_status === 'Contacted' ? form.call_back_date || null : null,
      description: form.description.trim(),
      task_name: props.taskId || null,
    })

    toast.success(__('Status update created successfully'))
    emit('updated', res)
    show.value = false
  } catch (err) {
    const msg =
      err.messages?.[0] || err.message || __('Failed to update status.')
    errorMessage.value = msg
    toast.error(msg)
  } finally {
    saving.value = false
  }
}
</script>
