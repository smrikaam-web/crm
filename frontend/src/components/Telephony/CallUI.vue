<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />

  <Dialog
    v-model:open="show"
    :title="__('Dial Pad')"
    :size="'sm'"
  >
    <template #default>
      <div class="flex flex-col gap-4 select-none">
        <!-- Number display & input field -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-ink-gray-5">
            {{ __('Phone Number') }}
          </label>
          <div class="relative flex items-center">
            <input
              ref="phoneInput"
              v-model="mobileNumber"
              type="tel"
              :placeholder="__('Enter phone number or dial')"
              class="w-full rounded-lg border border-surface-gray-4 bg-surface-white px-3 py-2.5 pr-16 text-lg font-semibold tracking-wider text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              @keydown.enter.prevent="makeCallUsing"
            />
            <div class="absolute right-1.5 flex items-center gap-1">
              <Button
                v-if="mobileNumber"
                variant="ghost"
                size="sm"
                class="!h-7 !w-7 !p-0 text-ink-gray-5 hover:text-ink-gray-8"
                :tooltip="__('Backspace')"
                @click="backspace"
              >
                <template #icon>
                  <svg
                    class="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
                    <line x1="18" y1="9" x2="12" y2="15" />
                    <line x1="12" y1="9" x2="18" y2="15" />
                  </svg>
                </template>
              </Button>
            </div>
          </div>
        </div>

        <!-- Numeric dial pad grid (0-9, *, #) -->
        <div class="grid grid-cols-3 gap-2 py-1">
          <button
            v-for="key in dialpadKeys"
            :key="key.digit"
            type="button"
            class="flex flex-col items-center justify-center h-12 rounded-lg border border-surface-gray-3 bg-surface-gray-2 hover:bg-surface-gray-3 active:bg-surface-gray-4 transition-colors focus:outline-none"
            @click="pressKey(key)"
          >
            <span class="text-base font-semibold leading-tight text-ink-gray-9">
              {{ key.digit }}
            </span>
            <span
              v-if="key.sub"
              class="text-[9px] font-medium tracking-widest text-ink-gray-5 uppercase leading-none"
            >
              {{ key.sub }}
            </span>
          </button>
        </div>

        <!-- Calling Medium selection (if multiple) -->
        <div
          v-if="enabledIntegrations.length > 1"
          class="flex flex-col gap-2 pt-1 border-t border-surface-gray-3"
        >
          <FormControl
            v-model="callMedium"
            type="select"
            :label="__('Calling Medium')"
            :options="['Twilio', 'Exotel']"
          />
          <FormControl
            v-model="isDefaultMedium"
            type="checkbox"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />
        </div>
        <div v-else class="flex items-center justify-between text-xs text-ink-gray-5 px-1">
          <span>{{ __('Calling medium') }}</span>
          <span class="font-medium text-ink-gray-8">{{ callMedium || 'Twilio' }}</span>
        </div>

        <!-- Action Buttons: Cancel and Call -->
        <div class="flex items-center gap-3 pt-2">
          <Button
            size="md"
            variant="subtle"
            theme="red"
            class="flex-1 justify-center rounded-lg"
            :label="__('Cancel')"
            @click="closeDialpad"
          />
          <Button
            size="md"
            variant="solid"
            theme="green"
            class="flex-1 justify-center rounded-lg text-ink-base font-medium"
            :label="__('Call')"
            :iconLeft="PhoneIcon"
            :loading="isMakingCall"
            :disabled="!mobileNumber || isMakingCall"
            @click="makeCallUsing"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import TwilioCallUI from '@/components/Telephony/TwilioCallUI.vue'
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { defaultCallingMedium, useTelephony } from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import {
  DIALPAD_KEYS,
  canInitiateCall,
  sanitizePhoneNumber,
} from '@/utils/twilioCall'
import { Button, Dialog, FormControl, call, toast } from 'frappe-ui'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const { setMakeCall } = globalStore()
const { isEnabled, isAnyEnabled } = useTelephony()

const twilio = ref(null)
const exotel = ref(null)
const phoneInput = ref(null)

const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')
const isMakingCall = ref(false)

const dialpadKeys = DIALPAD_KEYS

const enabledIntegrations = computed(() =>
  [
    { key: 'twilio', label: 'Twilio', ref: twilio },
    { key: 'exotel', label: 'Exotel', ref: exotel },
  ].filter(({ key }) => isEnabled(key)),
)

function isCallActive() {
  return Boolean(
    twilio.value?.isCallInProgress?.() ||
    exotel.value?.isCallInProgress?.()
  )
}

function pressKey(key) {
  mobileNumber.value = (mobileNumber.value || '') + key.digit
}

function backspace() {
  if (!mobileNumber.value) return
  mobileNumber.value = mobileNumber.value.slice(0, -1)
}

function closeDialpad() {
  show.value = false
  isMakingCall.value = false
}

function makeCall(number) {
  if (isCallActive() || isMakingCall.value) {
    toast.warning(__('A call is already in progress.'))
    return
  }

  mobileNumber.value = number ? String(number).trim() : ''

  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value
  } else if (enabledIntegrations.value.length > 0) {
    callMedium.value = enabledIntegrations.value[0]?.label ?? 'Twilio'
  }

  show.value = true
  nextTick(() => {
    phoneInput.value?.focus?.()
  })
}

async function makeCallUsing() {
  const rawNumber = mobileNumber.value ? mobileNumber.value.trim() : ''
  const check = canInitiateCall({
    isMakingCall: isMakingCall.value,
    isCallActive: isCallActive(),
    mobileNumber: rawNumber,
  })

  if (!check.canCall) {
    if (check.reason === 'missing_number' || check.reason === 'invalid_number') {
      toast.error(__('Please enter a valid phone number.'))
    } else if (
      check.reason === 'call_already_active' ||
      check.reason === 'call_already_initiating'
    ) {
      toast.warning(__('A call is already in progress.'))
    }
    return
  }

  isMakingCall.value = true

  try {
    if (isDefaultMedium.value && callMedium.value) {
      await setDefaultCallingMedium()
    }

    const numberToCall = sanitizePhoneNumber(rawNumber) || rawNumber

    // Close the dial pad dialog so active calling interface takes over
    show.value = false

    if (callMedium.value === 'Twilio') {
      await twilio.value?.makeOutgoingCall(numberToCall)
    } else if (callMedium.value === 'Exotel') {
      await exotel.value?.makeOutgoingCall(numberToCall)
    }
  } catch (error) {
    console.error('Failed to make call:', error)
  } finally {
    isMakingCall.value = false
  }
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

onMounted(() => {
  setMakeCall(makeCall)
})

watch(
  isAnyEnabled,
  () =>
    nextTick(() => {
      for (const {
        key,
        label,
        ref: integrationRef,
      } of enabledIntegrations.value) {
        integrationRef.value?.setup?.()
        callMedium.value = label
      }

      if (isAnyEnabled.value) {
        callMedium.value = enabledIntegrations.value[0]?.label ?? 'Twilio'
      }
      setMakeCall(makeCall)
    }),
  { immediate: true },
)
</script>
