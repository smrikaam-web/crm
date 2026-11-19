<template>
  <LayoutHeader v-if="contact.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <!-- Task Status Selector (when task is loaded) -->
      <div v-if="taskData" class="flex items-center gap-2">
        <span class="text-xs font-medium text-ink-gray-5">{{ __('Task Status:') }}</span>
        <select
          :value="taskData.status || 'To Do'"
          class="rounded-md border px-2.5 py-1 text-xs font-semibold focus:outline-none cursor-pointer transition-colors"
          :class="getStatusBadgeClass(taskData.status || 'To Do')"
          @change="changeTaskStatus($event.target.value)"
        >
          <option value="To Do">{{ __('To Do') }}</option>
          <option value="In Progress">{{ __('In Progress') }}</option>
          <option value="Pending">{{ __('Pending') }}</option>
          <option value="Callback">{{ __('Callback') }}</option>
          <option value="Follow up">{{ __('Follow up') }}</option>
          <option value="Not Interested">{{ __('Not Interested') }}</option>
        </select>
      </div>

      <CustomActions
        v-if="contact._actions?.length"
        :actions="contact._actions"
      />
      <Button
        variant="solid"
        :label="isAlreadyConverted ? __('View Lead') : __('Convert to Lead')"
        :iconLeft="isAlreadyConverted ? 'lucide-arrow-up-right' : 'lucide-user-check'"
        :loading="isConverting"
        :disabled="isConverting"
        @click="handleConvertToLead"
      />
    </template>
  </LayoutHeader>

  <div v-if="contact.doc" ref="parentRef" class="flex h-full">
    <!-- Left Side Panel (Matches Contact Detail Page) -->
    <Resizer
      v-if="contact.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeContactImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
                    :label="contact.doc.full_name"
                    :image="contact.doc.image"
                  />
                  <component
                    :is="contact.doc.image ? Dropdown : 'div'"
                    v-bind="
                      contact.doc.image
                        ? {
                            options: [
                              {
                                icon: 'lucide-upload',
                                label: contact.doc.image
                                  ? __('Change Image')
                                  : __('Upload Image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'lucide-trash-2',
                                label: __('Remove Image'),
                                onClick: () => changeContactImage(''),
                              },
                            ],
                          }
                        : { onClick: openFileSelector }
                    "
                    class="!absolute bottom-0 left-0 right-0"
                  >
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-1.5 truncate text-ink-gray-9">
                  <div class="truncate text-3xl-medium">
                    <span v-if="contact.doc.salutation">
                      {{ contact.doc.salutation + ' ' }}
                    </span>
                    <span>{{ contact.doc.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.doc.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    {{ contact.doc.company_name }}
                  </div>
                  <div
                    v-if="contact.doc.designation"
                    class="text-xs text-ink-gray-5"
                  >
                    {{ contact.doc.designation }}
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>

              <!-- Action buttons -->
              <div class="flex gap-1.5">
                <Button
                  :label="__('Make Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  class="font-medium"
                  @click="makeCall(contact.doc?.mobile_no || contact.doc?.phone || '')"
                />
              </div>

              <!-- Social Links (LinkedIn, Upwork, Website) -->
              <div class="w-full flex items-center justify-between pt-1 border-t border-outline-gray-1">
                <div class="flex items-center gap-2">
                  <!-- LinkedIn -->
                  <Tooltip :text="contact.doc?.custom_linkedin ? __('Open LinkedIn Profile') : __('LinkedIn URL not set')">
                    <button
                      type="button"
                      class="flex size-8 items-center justify-center rounded-md border transition-all duration-150"
                      :class="[
                        contact.doc?.custom_linkedin
                          ? 'border-outline-gray-2 bg-surface-white text-[#0A66C2] hover:bg-surface-blue-2 hover:border-outline-blue-2 shadow-xs cursor-pointer'
                          : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                      ]"
                      :disabled="!contact.doc?.custom_linkedin"
                      @click="contact.doc?.custom_linkedin && openExternalUrl(contact.doc.custom_linkedin)"
                    >
                      <LinkedInIcon class="size-4.5" />
                    </button>
                  </Tooltip>

                  <!-- Upwork -->
                  <Tooltip :text="contact.doc?.custom_upwork ? __('Open Upwork Profile') : __('Upwork URL not set')">
                    <button
                      type="button"
                      class="flex size-8 items-center justify-center rounded-md border transition-all duration-150"
                      :class="[
                        contact.doc?.custom_upwork
                          ? 'border-outline-gray-2 bg-surface-white text-[#14A800] hover:bg-surface-green-2 hover:border-outline-green-2 shadow-xs cursor-pointer'
                          : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                      ]"
                      :disabled="!contact.doc?.custom_upwork"
                      @click="contact.doc?.custom_upwork && openExternalUrl(contact.doc.custom_upwork)"
                    >
                      <UpworkIcon class="size-4.5" />
                    </button>
                  </Tooltip>

                  <!-- Website -->
                  <Tooltip :text="contact.doc?.custom_website ? __('Open Website') : __('Website URL not set')">
                    <button
                      type="button"
                      class="flex size-8 items-center justify-center rounded-md border transition-all duration-150"
                      :class="[
                        contact.doc?.custom_website
                          ? 'border-outline-gray-2 bg-surface-white text-ink-gray-8 hover:bg-surface-gray-2 hover:border-outline-gray-3 shadow-xs cursor-pointer'
                          : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                      ]"
                      :disabled="!contact.doc?.custom_website"
                      @click="contact.doc?.custom_website && openExternalUrl(contact.doc.custom_website)"
                    >
                      <WebsiteIcon class="size-4.5" />
                    </button>
                  </Tooltip>
                </div>

                <!-- Edit Social Links Button -->
                <Tooltip :text="__('Edit Social Links')">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon="lucide-edit-2"
                    class="text-ink-gray-5 hover:text-ink-gray-9 !size-7"
                    @click="showSocialModal = true"
                  />
                </Tooltip>
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>

    <!-- Right Side Activities Panel with allowEmail=true and showUpdateStatus=true -->
    <ContactActivities
      ref="contactActivitiesRef"
      :contact="contact.doc"
      :contactId="decodedContactId"
      :taskId="taskData?.name || props.taskId"
      :allowEmail="true"
      :showUpdateStatus="true"
      :dealRows="rows"
      :dealColumns="columns"
      @newDeal="openDealModal"
      @taskStatusUpdated="onTaskStatusUpdated"
    />
  </div>
  <div v-else-if="contact.loading" class="flex h-full w-full items-center justify-center">
    <LoadingIndicator class="w-8 h-8 text-ink-gray-5" />
  </div>
  <ErrorPage
    v-else-if="errorTitle || contact.error"
    :errorTitle="errorTitle || __('Error Occurred')"
    :errorMessage="errorMessage || contact.error?.messages?.[0] || __('Could not load prospect details.')"
  />
  <div v-else class="flex h-full w-full items-center justify-center text-ink-gray-5 text-sm">
    <LoadingIndicator class="w-6 h-6 mr-2 text-ink-gray-5" />
    <span>{{ __('Loading prospect...') }}</span>
  </div>
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="dealDefaults"
  />

  <!-- Edit Social Links Modal -->
  <Dialog v-model:open="showSocialModal" :size="'sm'">
    <template #title>
      <div class="text-base font-semibold text-ink-gray-9">{{ __('Edit Social Links') }}</div>
    </template>
    <template #default>
      <div class="space-y-3.5 py-1">
        <div>
          <label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('LinkedIn Profile URL') }}</label>
          <input
            v-model="socialForm.linkedin"
            type="url"
            class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs focus:border-outline-gray-4 focus:outline-none"
            placeholder="https://www.linkedin.com/in/username"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Upwork Profile URL') }}</label>
          <input
            v-model="socialForm.upwork"
            type="url"
            class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs focus:border-outline-gray-4 focus:outline-none"
            placeholder="https://www.upwork.com/freelancers/..."
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Website URL') }}</label>
          <input
            v-model="socialForm.website"
            type="url"
            class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs focus:border-outline-gray-4 focus:outline-none"
            placeholder="https://example.com"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="subtle" :label="__('Cancel')" @click="showSocialModal = false" />
        <Button variant="solid" :label="__('Save Links')" :loading="savingSocial" @click="saveSocialLinks" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LinkedInIcon from '@/components/Icons/LinkedInIcon.vue'
import UpworkIcon from '@/components/Icons/UpworkIcon.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import ContactActivities from '@/components/ContactActivities/ContactActivities.vue'
import CustomActions from '@/components/CustomActions.vue'
import { validateIsImageFile, setupCustomizations } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
  Tooltip,
  Dialog,
  Button,
  LoadingIndicator,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
  taskId: { type: [String, Number], default: null },
})

const route = useRoute()
const router = useRouter()

const decodedContactId = (() => {
  try {
    return decodeURIComponent(props.contactId || '')
  } catch (e) {
    return props.contactId || ''
  }
})()

const errorTitle = ref('')
const errorMessage = ref('')
const taskData = ref(null)

// Instant preload from cached task if navigating from My Tasks
if (props.taskId) {
  try {
    const cached = sessionStorage.getItem('active_task_' + props.taskId)
    if (cached) {
      taskData.value = JSON.parse(cached)
    }
  } catch (e) {}
}

const {
  document: contact,
  permissions,
  scripts,
  error,
  triggerOnRender,
} = useDocument('Contact', decodedContactId)

watch(
  error,
  (err) => {
    if (err) {
      errorTitle.value = __(
        err.exc_type === 'DoesNotExistError'
          ? __('Prospect Not Found')
          : __('Error Occurred'),
      )
      errorMessage.value = __(
        err.messages?.[0] ||
          err.message ||
          __('An error occurred while loading this prospect.'),
      )
    } else {
      errorTitle.value = ''
      errorMessage.value = ''
    }
  },
  { immediate: true },
)

const transformField = useContactFields(contact)

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}

async function fetchTaskDetails() {
  try {
    const res = await call('crm.api.daily_allocation.get_task_for_contact', {
      contact: decodedContactId,
      task_name: props.taskId || null,
    })
    if (res) {
      taskData.value = res
    }
  } catch (err) {
    console.error('Failed to load task details:', err)
  }
}

// Fire fetchTaskDetails in parallel with useDocument
fetchTaskDetails()

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  return [
    { label: __('My Tasks'), route: { name: 'Tasks' } },
    {
      label: title.value,
      route: {
        name: 'TaskProspect',
        params: { contactId: decodedContactId },
        query: route.query,
      },
    },
  ]
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || decodedContactId
})

usePageMeta(() => {
  return {
    title: `${title.value} — My Tasks`,
    icon: brand.favicon,
  }
})

const showDealModal = ref(false)
const dealDefaults = ref({})
const contactActivitiesRef = ref(null)

async function changeTaskStatus(newStatus) {
  if (!taskData.value?.name) return
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: taskData.value.name,
      status: newStatus,
    })
    taskData.value.status = newStatus
    toast.success(__('Task status updated to {0}', [newStatus]))
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to update status'))
  }
}

function onTaskStatusUpdated(newStatus) {
  if (taskData.value) {
    taskData.value.status = newStatus
  }
}

function getStatusBadgeClass(st) {
  switch (st) {
    case 'To Do':
      return 'bg-surface-gray-2 text-ink-gray-7 border-outline-gray-2'
    case 'In Progress':
      return 'bg-surface-blue-2 text-ink-blue-4 border-outline-blue-2'
    case 'Pending':
      return 'bg-surface-amber-2 text-ink-amber-5 border-outline-amber-2'
    case 'Callback':
      return 'bg-surface-purple-2 text-ink-purple-4 border-outline-purple-2'
    case 'Follow up':
      return 'bg-surface-teal-2 text-ink-teal-4 border-outline-teal-2'
    case 'Not Interested':
      return 'bg-surface-gray-3 text-ink-gray-6 border-outline-gray-3'
    default:
      return 'bg-surface-gray-2 text-ink-gray-7 border-outline-gray-2'
  }
}

// company_name is free text, so only pick an existing organization; otherwise the deal creates one
async function openDealModal() {
  const company = contact.doc.company_name
  const isOrganization =
    company &&
    (await call('frappe.client.get_count', {
      doctype: 'CRM Organization',
      filters: { name: company },
    }))
  dealDefaults.value = {
    contact: contact.doc.name,
    ...(isOrganization
      ? { organization: company }
      : { organization_name: company }),
  }
  showDealModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

const rows = computed(() => [])

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data
    .map((section) => ({
      ...section,
      columns: section.columns
        .map((column) => ({
          ...column,
          fields: column.fields
            .filter((field) => ['email_id', 'mobile_no'].includes(field.fieldname))
            .map((field) => {
              if (field.fieldname === 'email_id') {
                field.label = __('Email Address')
                field.placeholder = __('Add Email Address...')
              } else if (field.fieldname === 'mobile_no') {
                field.label = __('Mobile Number')
                field.placeholder = __('Add Mobile Number...')
              } else {
                field.label = fieldLabelMap[field.fieldname] || field.label
                field.placeholder =
                  fieldPlaceholderMap[field.fieldname] || field.placeholder
              }
              return transformField(field, { showAddressModal })
            }),
        }))
        .filter((column) => column.fields.length > 0),
    }))
    .filter((section) => section.columns.length > 0)
})

const isConverting = ref(false)

const isAlreadyConverted = computed(() => {
  return Boolean(contact.doc?.custom_converted_lead)
})

async function handleConvertToLead() {
  if (isAlreadyConverted.value) {
    const leadId = contact.doc.custom_converted_lead
    toast.info(__('Opening converted Lead {0}', [leadId]))
    router.push({ name: 'Lead', params: { leadId } })
    return
  }

  isConverting.value = true
  try {
    const res = await call('crm.api.contact.convert_contact_to_lead', {
      contact: decodedContactId,
      task_name: taskData.value?.name || props.taskId || null,
    })
    if (res?.lead_name) {
      if (contact.doc) {
        contact.doc.custom_converted_lead = res.lead_name
      }
      if (res.already_converted) {
        toast.info(res.message || __('This prospect is already converted to Lead {0}.', [res.lead_name]))
      } else {
        toast.success(res.message || __('Prospect converted to Lead successfully.'))
      }
      router.push({ name: 'Lead', params: { leadId: res.lead_name } })
    }
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to convert prospect to Lead.'))
  } finally {
    isConverting.value = false
  }
}

function openExternalUrl(url) {
  if (!url) return
  const fullUrl = url.startsWith('http://') || url.startsWith('https://') ? url : `https://${url}`
  window.open(fullUrl, '_blank')
}

const showSocialModal = ref(false)
const savingSocial = ref(false)
const socialForm = reactive({
  linkedin: '',
  upwork: '',
  website: '',
})

watch(
  () => showSocialModal.value,
  (open) => {
    if (open && contact.doc) {
      socialForm.linkedin = contact.doc.custom_linkedin || ''
      socialForm.upwork = contact.doc.custom_upwork || ''
      socialForm.website = contact.doc.custom_website || ''
    }
  },
)

async function saveSocialLinks() {
  savingSocial.value = true
  try {
    const res = await call('crm.api.contact.update_contact_social_links', {
      contact: decodedContactId,
      linkedin: socialForm.linkedin,
      upwork: socialForm.upwork,
      website: socialForm.website,
    })
    if (contact.doc) {
      contact.doc.custom_linkedin = res.custom_linkedin
      contact.doc.custom_upwork = res.custom_upwork
      contact.doc.custom_website = res.custom_website
    }
    toast.success(__('Social links updated successfully'))
    showSocialModal.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to update social links'))
  } finally {
    savingSocial.value = false
  }
}

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: contact.setValue.submit,
        deleteDoc: () => {},
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>

