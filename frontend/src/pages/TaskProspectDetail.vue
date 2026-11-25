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
      <!-- Task Status Selector -->
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
      <!-- Convert to Lead Action Button: Dark navy button matching reference image -->
      <Button
        variant="solid"
        class="!bg-[#18202f] !text-white hover:!bg-[#253248] shadow-xs"
        :label="isAlreadyConverted ? __('View Lead') : __('Convert to Lead')"
        :iconLeft="isAlreadyConverted ? 'lucide-arrow-up-right' : 'lucide-user-check'"
        :loading="isConverting"
        :disabled="isConverting"
        @click="handleConvertToLead"
      />
    </template>
  </LayoutHeader>

  <!-- 3-Column Page Layout Matching Reference Image -->
  <div v-if="contact.doc" class="flex h-[calc(100vh-50px)] overflow-hidden bg-surface-gray-1 dark:bg-surface-gray-9">
    <!-- LEFT COLUMN: Profile, Contact Info, Details (Width ~330px) -->
    <div class="w-[330px] shrink-0 border-r border-outline-gray-2 bg-surface-base p-4 overflow-y-auto space-y-3.5 dark:border-outline-gray-7 dark:bg-surface-gray-9">
      <!-- 1. Prospect Profile Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-3 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <div class="flex items-center gap-3">
          <div class="size-12 rounded-full overflow-hidden bg-surface-gray-3 flex items-center justify-center text-lg font-bold text-ink-gray-8 uppercase dark:bg-surface-gray-7 dark:text-ink-white shrink-0 shadow-2xs border border-outline-gray-2 dark:border-outline-gray-7">
            <img
              v-if="prospectCountryIso && !flagLoadError"
              :src="`https://flagcdn.com/w80/${prospectCountryIso}.png`"
              :alt="prospectCountry"
              class="size-full object-cover"
              loading="eager"
              @error="flagLoadError = true"
            />
            <span v-else>
              {{ contact.doc.full_name?.charAt(0) || 'P' }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="truncate text-base font-bold text-ink-gray-9 dark:text-ink-white leading-tight" :title="contact.doc.full_name">
              {{ contact.doc.full_name }}
            </h2>
            <p v-if="contact.doc.company_name" class="truncate text-xs text-ink-gray-5 dark:text-ink-gray-4 mt-0.5" :title="contact.doc.company_name">
              {{ contact.doc.company_name }}
            </p>
          </div>
        </div>

        <!-- Social Icons Row -->
        <div class="flex items-center justify-between pt-1 border-t border-outline-gray-1 dark:border-outline-gray-7">
          <div class="flex items-center gap-2">
            <!-- LinkedIn -->
            <Tooltip :text="contact.doc?.custom_linkedin ? __('Open LinkedIn Profile') : __('LinkedIn URL not set')">
              <button
                type="button"
                class="flex size-7 items-center justify-center rounded-md border transition-all"
                :class="[
                  contact.doc?.custom_linkedin
                    ? 'border-blue-200 bg-blue-50 text-[#0A66C2] hover:bg-blue-100 cursor-pointer shadow-2xs'
                    : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                ]"
                :disabled="!contact.doc?.custom_linkedin"
                @click="contact.doc?.custom_linkedin && openExternalUrl(contact.doc.custom_linkedin)"
              >
                <LinkedInIcon class="size-3.5" />
              </button>
            </Tooltip>

            <!-- Website / Globe -->
            <Tooltip :text="contact.doc?.custom_website ? __('Open Website') : __('Website URL not set')">
              <button
                type="button"
                class="flex size-7 items-center justify-center rounded-md border transition-all"
                :class="[
                  contact.doc?.custom_website
                    ? 'border-outline-gray-3 bg-surface-white text-ink-gray-7 hover:bg-surface-gray-2 cursor-pointer shadow-2xs'
                    : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                ]"
                :disabled="!contact.doc?.custom_website"
                @click="contact.doc?.custom_website && openExternalUrl(contact.doc.custom_website)"
              >
                <WebsiteIcon class="size-3.5" />
              </button>
            </Tooltip>

            <!-- Upwork -->
            <Tooltip :text="contact.doc?.custom_upwork ? __('Open Upwork Profile') : __('Upwork URL not set')">
              <button
                type="button"
                class="flex size-7 items-center justify-center rounded-md border transition-all"
                :class="[
                  contact.doc?.custom_upwork
                    ? 'border-green-200 bg-green-50 text-[#14A800] hover:bg-green-100 cursor-pointer shadow-2xs'
                    : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-4 opacity-50 cursor-not-allowed',
                ]"
                :disabled="!contact.doc?.custom_upwork"
                @click="contact.doc?.custom_upwork && openExternalUrl(contact.doc.custom_upwork)"
              >
                <UpworkIcon class="size-3.5" />
              </button>
            </Tooltip>
          </div>

          <!-- Edit Social Links Pencil -->
          <Tooltip :text="__('Edit Social Links')">
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-edit-2"
              class="!size-6 text-ink-gray-4 hover:text-ink-gray-8"
              @click="showSocialModal = true"
            />
          </Tooltip>
        </div>

        <!-- Dynamic Greeting & Local Time Row -->
        <div class="flex items-center gap-1.5 text-xs text-ink-gray-6 bg-surface-gray-1 px-2.5 py-1.5 rounded-lg dark:bg-surface-gray-7 dark:text-ink-gray-3">
          <span class="lucide-clock size-3.5 text-ink-gray-5 shrink-0" />
          <span class="truncate">{{ prospectLocalTime.display }}</span>
        </div>
      </div>

      <!-- 2. Contact Info Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-3 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <h3 class="text-xs font-bold uppercase tracking-wider text-ink-gray-9 dark:text-ink-white">{{ __('Contact Info') }}</h3>

        <!-- Primary Phone -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="lucide-phone size-4 text-ink-gray-5 shrink-0" />
            <div class="min-w-0">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Primary Number') }}</div>
              <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white truncate" :title="primaryPhone">
                {{ primaryPhone || '—' }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="primaryPhone"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Call')"
              @click="handleCall(primaryPhone)"
            >
              <span class="lucide-phone size-3 text-emerald-600" />
            </button>
            <button
              v-if="primaryPhone"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Copy')"
              @click="copyToClipboard(primaryPhone, __('Phone number'))"
            >
              <span class="lucide-copy size-3 text-ink-gray-5" />
            </button>
          </div>
        </div>

        <!-- Secondary Phone -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="lucide-phone size-4 text-ink-gray-5 shrink-0" />
            <div class="min-w-0">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Secondary Number') }}</div>
              <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white truncate" :title="secondaryPhone">
                {{ secondaryPhone || '—' }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="secondaryPhone"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Call')"
              @click="handleCall(secondaryPhone)"
            >
              <span class="lucide-phone size-3 text-emerald-600" />
            </button>
            <button
              v-if="secondaryPhone"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Copy')"
              @click="copyToClipboard(secondaryPhone, __('Phone number'))"
            >
              <span class="lucide-copy size-3 text-ink-gray-5" />
            </button>
          </div>
        </div>

        <!-- Primary Email -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="lucide-mail size-4 text-ink-gray-5 shrink-0" />
            <div class="min-w-0">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Primary Email') }}</div>
              <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white truncate" :title="primaryEmail">
                {{ primaryEmail || '—' }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="primaryEmail"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Copy')"
              @click="copyToClipboard(primaryEmail, __('Email address'))"
            >
              <span class="lucide-copy size-3 text-ink-gray-5" />
            </button>
          </div>
        </div>

        <!-- Secondary Email -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="lucide-mail size-4 text-ink-gray-5 shrink-0" />
            <div class="min-w-0">
              <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Secondary Email') }}</div>
              <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white truncate" :title="secondaryEmail">
                {{ secondaryEmail || '—' }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="secondaryEmail"
              type="button"
              class="size-6 flex items-center justify-center rounded hover:bg-surface-gray-2 text-ink-gray-6 cursor-pointer"
              :title="__('Copy')"
              @click="copyToClipboard(secondaryEmail, __('Email address'))"
            >
              <span class="lucide-copy size-3 text-ink-gray-5" />
            </button>
          </div>
        </div>

        <!-- Country -->
        <div class="flex items-center gap-2.5">
          <span class="lucide-map-pin size-4 text-ink-gray-5 shrink-0" />
          <div>
            <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Country') }}</div>
            <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white">
              {{ contact.doc.country || taskData?.country || '—' }}
            </div>
          </div>
        </div>

        <!-- Timezone -->
        <div class="flex items-center gap-2.5">
          <span class="lucide-clock size-4 text-ink-gray-5 shrink-0" />
          <div>
            <div class="text-[10px] font-semibold uppercase tracking-wider text-ink-gray-4">{{ __('Timezone') }}</div>
            <div class="text-xs font-medium text-ink-gray-9 dark:text-ink-white">
              {{ prospectTimezoneDisplay }}
            </div>
          </div>
        </div>

        <!-- Active Call Controls Card in Prospect Detail -->
        <div
          v-if="isCallActive"
          class="rounded-xl border border-slate-700/60 bg-[#172133] p-3 text-white shadow-md space-y-2.5 mt-2"
        >
          <!-- Call Status & Live Timer -->
          <div class="flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-emerald-400 animate-pulse" />
              <span class="font-semibold text-slate-200">
                {{ callState.status === 'initiating' ? __('Connecting...') : callState.status === 'ringing' ? __('Ringing...') : __('On Call') }}
              </span>
            </div>
            <span v-if="callState.onCall" class="font-mono text-emerald-400 text-xs font-semibold">
              {{ callState.duration || '00:00:00' }}
            </span>
          </div>

          <!-- Prospect Phone under call -->
          <div class="text-xs text-slate-300 truncate">
            {{ callState.phoneNumber || primaryPhone }}
          </div>

          <!-- Controls: Mute, Keypad, Notes, End Call / Cancel -->
          <div class="flex items-center justify-between gap-1.5 pt-1">
            <!-- Mute/Unmute (Only when connected) -->
            <button
              v-if="callState.onCall"
              type="button"
              class="flex size-8 items-center justify-center rounded-full transition-colors cursor-pointer"
              :class="callState.muted ? 'bg-red-600 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'"
              :title="callState.muted ? __('Unmute') : __('Mute')"
              @click="toggleMute"
            >
              <LucideMicOff v-if="callState.muted" class="size-3.5" />
              <LucideMic v-else class="size-3.5" />
            </button>

            <!-- Keypad (DTMF) (Only when connected) -->
            <button
              v-if="callState.onCall"
              type="button"
              class="flex size-8 items-center justify-center rounded-full transition-colors cursor-pointer"
              :class="showDetailKeypad ? 'bg-slate-500 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'"
              :title="__('Keypad')"
              @click="showDetailKeypad = !showDetailKeypad"
            >
              <DialpadIcon class="size-3.5" />
            </button>

            <!-- Notes (Only when connected) -->
            <button
              v-if="callState.onCall"
              type="button"
              class="flex size-8 items-center justify-center rounded-full bg-slate-700/80 text-slate-200 hover:bg-slate-600 cursor-pointer"
              :title="__('Notes')"
              @click="showDetailNotes = !showDetailNotes"
            >
              <LucideFileText class="size-3.5" />
            </button>

            <!-- End Call / Cancel -->
            <button
              type="button"
              class="flex items-center justify-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-xs transition-colors cursor-pointer ml-auto"
              :class="callState.onCall ? 'bg-red-600 hover:bg-red-700' : 'bg-red-600/80 hover:bg-red-700'"
              @click="endCall"
            >
              <PhoneIcon class="size-3.5 rotate-[135deg]" />
              <span>{{ callState.onCall ? __('End Call') : __('Cancel') }}</span>
            </button>
          </div>

          <!-- Inline DTMF Keypad (Collapsible) -->
          <div
            v-if="callState.onCall && showDetailKeypad"
            class="grid grid-cols-3 gap-1 rounded-lg bg-slate-800/80 p-1.5 pt-2"
          >
            <button
              v-for="digit in dtmfDigits"
              :key="digit"
              type="button"
              class="h-7 rounded bg-slate-700/50 text-xs font-semibold text-white hover:bg-slate-600 cursor-pointer"
              @click="sendDigit(digit)"
            >
              {{ digit }}
            </button>
          </div>

          <!-- Inline Notes (Collapsible) -->
          <div
            v-if="callState.onCall && showDetailNotes"
            class="pt-1.5"
          >
            <textarea
              v-model="detailCallNotes"
              rows="3"
              :placeholder="__('Add notes during call...')"
              class="w-full resize-none rounded-lg border border-slate-700 bg-slate-800/80 p-2 text-xs text-white placeholder:text-slate-400 focus:outline-none"
              @input="handleDetailNotesInput"
            />
          </div>
        </div>

        <!-- Large Full-width Call Button (When Idle) -->
        <div v-else class="pt-2">
          <button
            type="button"
            class="w-full py-2.5 px-4 rounded-lg bg-[#18202f] hover:bg-[#253248] text-white flex items-center justify-center gap-2 text-xs font-bold transition-colors shadow-xs cursor-pointer disabled:opacity-50"
            :disabled="!primaryPhone && !secondaryPhone"
            @click="handleCall(primaryPhone || secondaryPhone)"
          >
            <span class="lucide-phone size-3.5" />
            <span>{{ __('Call') }}</span>
          </button>
        </div>
      </div>

      <!-- 3. Details Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-2.5 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <h3 class="text-xs font-bold uppercase tracking-wider text-ink-gray-9 dark:text-ink-white mb-2">{{ __('Details') }}</h3>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Designation') }}</span>
          <span class="font-medium text-ink-gray-9 dark:text-ink-white text-right max-w-[60%] truncate" :title="contact.doc.designation">
            {{ contact.doc.designation || '—' }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Lead Source') }}</span>
          <span class="font-medium text-ink-gray-9 dark:text-ink-white">
            {{ contact.doc.lead_source || contact.doc.source || 'Website' }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Status') }}</span>
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
            {{ taskData?.status || 'Contacted' }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Owner') }}</span>
          <span class="font-medium text-ink-gray-9 dark:text-ink-white">
            {{ leadOwnerName }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Data Age') }}</span>
          <span class="font-medium text-ink-gray-9 dark:text-ink-white">
            {{ dataAgeDisplay }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-ink-gray-5">{{ __('Last Updated') }}</span>
          <span class="font-medium text-ink-gray-9 dark:text-ink-white">
            {{ lastUpdatedDisplay }}
          </span>
        </div>
      </div>
    </div>

    <!-- CENTER COLUMN: Activity Feed & Tabs (flex-1) -->
    <div class="flex-1 min-w-0 flex flex-col bg-surface-white border-r border-outline-gray-2 overflow-hidden dark:bg-surface-gray-8 dark:border-outline-gray-7">
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

    <!-- RIGHT COLUMN: Team on this contact, Related Organization, Other People (Width ~290px) -->
    <div class="w-[290px] shrink-0 bg-surface-base p-4 overflow-y-auto space-y-3.5 dark:bg-surface-gray-9">
      <!-- 1. Team on this Contact Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-3 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <h3 class="text-[11px] font-bold uppercase tracking-wider text-ink-gray-5 dark:text-ink-gray-4">
          {{ __('Team on this contact') }}
        </h3>

        <!-- Lead Owner -->
        <div class="flex items-center gap-3">
          <div class="size-8 rounded-full bg-violet-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
            {{ getInitials(leadOwnerName) }}
          </div>
          <div class="min-w-0">
            <div class="text-xs font-bold text-ink-gray-9 dark:text-ink-white truncate">{{ leadOwnerName }}</div>
            <div class="text-[11px] text-ink-gray-5">{{ __('Lead owner') }}</div>
          </div>
        </div>

        <!-- Assigned By -->
        <div class="flex items-center gap-3">
          <div class="size-8 rounded-full bg-surface-gray-4 text-ink-gray-7 flex items-center justify-center text-xs font-bold dark:bg-surface-gray-7 dark:text-ink-gray-2 shrink-0">
            {{ getInitials(assignedByName) }}
          </div>
          <div class="min-w-0">
            <div class="text-xs font-bold text-ink-gray-9 dark:text-ink-white truncate">{{ assignedByName }}</div>
            <div class="text-[11px] text-ink-gray-5">{{ __('Assigned by') }}</div>
          </div>
        </div>
      </div>

      <!-- 2. Related Organization Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-2 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <h3 class="text-[11px] font-bold uppercase tracking-wider text-ink-gray-5 dark:text-ink-gray-4">
          {{ __('Related Organization') }}
        </h3>

        <div class="flex items-center gap-3 pt-1">
          <div class="size-8 rounded-lg bg-surface-gray-2 flex items-center justify-center text-ink-gray-6 border border-outline-gray-2 dark:bg-surface-gray-7 dark:border-outline-gray-6 dark:text-ink-gray-3 shrink-0">
            <span class="lucide-building-2 size-4" />
          </div>
          <div class="min-w-0">
            <div class="text-xs font-bold text-ink-gray-9 dark:text-ink-white truncate" :title="contact.doc.company_name">
              {{ contact.doc.company_name || 'Smrikaam Technologies' }}
            </div>
            <div class="text-[11px] text-ink-gray-5">{{ __('Organisation') }}</div>
          </div>
        </div>
      </div>

      <!-- 3. Other People at Company Card -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xs space-y-3 dark:border-outline-gray-7 dark:bg-surface-gray-8">
        <div class="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-ink-gray-5 dark:text-ink-gray-4">
          <span class="lucide-users size-3.5 shrink-0" />
          <span class="truncate">{{ __('Other people at {0}', [contact.doc.company_name || 'Organization']) }}</span>
        </div>

        <div class="space-y-2.5">
          <div
            v-for="(colleague, idx) in colleaguesList"
            :key="colleague.name"
            class="flex items-center gap-3 py-0.5"
          >
            <div
              class="size-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
              :class="colleagueColors[idx % colleagueColors.length]"
            >
              {{ getInitials(colleague.full_name) }}
            </div>
            <div class="min-w-0">
              <div class="text-xs font-bold text-ink-gray-9 dark:text-ink-white truncate">
                {{ colleague.full_name }}
              </div>
              <div class="text-[11px] text-ink-gray-5 truncate">
                {{ colleague.designation || __('Colleague') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import LinkedInIcon from '@/components/Icons/LinkedInIcon.vue'
import UpworkIcon from '@/components/Icons/UpworkIcon.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import LucideMic from '~icons/lucide/mic'
import LucideMicOff from '~icons/lucide/mic-off'
import LucideFileText from '~icons/lucide/file-text'
import DealModal from '@/components/Modals/DealModal.vue'
import ContactActivities from '@/components/ContactActivities/ContactActivities.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations } from '@/utils'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { useTelephonyCall } from '@/composables/useTelephonyCall'
import {
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  Tooltip,
  Dialog,
  Button,
  LoadingIndicator,
} from 'frappe-ui'
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()
const { doctypeMeta } = getMeta('Contact')
const {
  state: callState,
  isCallActive,
  initiateCall,
  endCall,
  toggleMute,
  sendDigit,
  updateNotes,
} = useTelephonyCall()

const showDetailKeypad = ref(false)
const showDetailNotes = ref(false)
const detailCallNotes = computed({
  get: () => callState.notes || '',
  set: (val) => {
    callState.notes = val
  },
})
const dtmfDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

let detailNotesTimeout = null
function handleDetailNotesInput() {
  if (detailNotesTimeout) clearTimeout(detailNotesTimeout)
  detailNotesTimeout = setTimeout(() => {
    updateNotes(detailCallNotes.value)
  }, 400)
}

function handleCall(number) {
  if (!number) return
  initiateCall(number, {
    name: contact.doc?.name,
    full_name: contact.doc?.full_name,
    organization: contact.doc?.company_name,
    designation: contact.doc?.designation,
    mobile_no: number,
    image: contact.doc?.image,
  })
}

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

fetchTaskDetails()

const currentTime = ref(new Date())
let timerInterval = null

onMounted(async () => {
  timerInterval = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)

  if (contact.doc) {
    await triggerOnRender()
    fetchColleagues()
  }
})

onBeforeUnmount(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (detailNotesTimeout) clearTimeout(detailNotesTimeout)
})

watch(
  () => contact.doc?.company_name,
  () => {
    if (contact.doc?.company_name) {
      fetchColleagues()
    }
  },
)

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

function copyToClipboard(val, label = 'Text') {
  if (!val || val === '—') return
  navigator.clipboard.writeText(val).then(() => {
    toast.success(__('{0} copied to clipboard', [label]))
  }).catch(() => {
    toast.error(__('Failed to copy to clipboard'))
  })
}

// Phone & Email Getters
const primaryPhone = computed(() => contact.doc?.mobile_no || '')
const secondaryPhone = computed(() => contact.doc?.phone || contact.doc?.custom_secondary_phone || '')
const primaryEmail = computed(() => contact.doc?.email_id || '')
const secondaryEmail = computed(() => contact.doc?.custom_secondary_email || contact.doc?.alternate_email || '')

// Team Members
const leadOwnerName = computed(() => {
  return taskData.value?.assigned_to_name || contact.doc?.owner_name || contact.doc?.owner || 'Sam Walker'
})

const assignedByName = computed(() => {
  return taskData.value?.allocated_by_name || 'Manoj kumar'
})

// Country Flag Mapping & Resolution
const flagLoadError = ref(false)

watch(
  () => contact.doc?.country,
  () => {
    flagLoadError.value = false
  },
)

const countryToIsoMap = {
  // Austria
  'austria': 'at',
  'at': 'at',
  'österreich': 'at',
  // India
  'india': 'in',
  'in': 'in',
  'bharat': 'in',
  // United States
  'united states': 'us',
  'united states of america': 'us',
  'usa': 'us',
  'us': 'us',
  // United Kingdom
  'united kingdom': 'gb',
  'uk': 'gb',
  'gb': 'gb',
  'great britain': 'gb',
  'england': 'gb',
  'scotland': 'gb',
  'wales': 'gb',
  // Germany
  'germany': 'de',
  'de': 'de',
  'deutschland': 'de',
  // Singapore
  'singapore': 'sg',
  'sg': 'sg',
  // Saudi Arabia
  'saudi arabia': 'sa',
  'sa': 'sa',
  'ksa': 'sa',
  // UAE
  'united arab emirates': 'ae',
  'uae': 'ae',
  'ae': 'ae',
  // France
  'france': 'fr',
  'fr': 'fr',
  // Australia
  'australia': 'au',
  'au': 'au',
  // Canada
  'canada': 'ca',
  'ca': 'ca',
  // Switzerland
  'switzerland': 'ch',
  'ch': 'ch',
  'schweiz': 'ch',
  'suisse': 'ch',
  // Netherlands
  'netherlands': 'nl',
  'nl': 'nl',
  'holland': 'nl',
  // Ireland
  'ireland': 'ie',
  'ie': 'ie',
  // Sweden
  'sweden': 'se',
  'se': 'se',
  // Norway
  'norway': 'no',
  'no': 'no',
  // Denmark
  'denmark': 'dk',
  'dk': 'dk',
  // Finland
  'finland': 'fi',
  'fi': 'fi',
  // Italy
  'italy': 'it',
  'it': 'it',
  'italia': 'it',
  // Spain
  'spain': 'es',
  'es': 'es',
  'españa': 'es',
  // New Zealand
  'new zealand': 'nz',
  'nz': 'nz',
  // Japan
  'japan': 'jp',
  'jp': 'jp',
  // China
  'china': 'cn',
  'cn': 'cn',
  // Brazil
  'brazil': 'br',
  'br': 'br',
  'brasil': 'br',
  // Mexico
  'mexico': 'mx',
  'mx': 'mx',
  // South Africa
  'south africa': 'za',
  'za': 'za',
  // Belgium
  'belgium': 'be',
  'be': 'be',
  // Portugal
  'portugal': 'pt',
  'pt': 'pt',
  // Poland
  'poland': 'pl',
  'pl': 'pl',
  // Russia
  'ru': 'ru',
  'russia': 'ru',
  // Turkey
  'turkey': 'tr',
  'türkiye': 'tr',
  'tr': 'tr',
  // Argentina
  'argentina': 'ar',
  'ar': 'ar',
  // Chile
  'chile': 'cl',
  'cl': 'cl',
  // Colombia
  'colombia': 'co',
  'co': 'co',
  // Egypt
  'egypt': 'eg',
  'eg': 'eg',
  // Indonesia
  'indonesia': 'id',
  'id': 'id',
  // Israel
  'israel': 'il',
  'il': 'il',
  // Malaysia
  'malaysia': 'my',
  'my': 'my',
  // Nigeria
  'nigeria': 'ng',
  'ng': 'ng',
  // Pakistan
  'pakistan': 'pk',
  'pk': 'pk',
  // Philippines
  'philippines': 'ph',
  'ph': 'ph',
  // Qatar
  'qatar': 'qa',
  'qa': 'qa',
  // South Korea
  'south korea': 'kr',
  'korea': 'kr',
  'kr': 'kr',
  // Thailand
  'thailand': 'th',
  'th': 'th',
  // Ukraine
  'ua': 'ua',
  'ukraine': 'ua',
  // Vietnam
  'vietnam': 'vn',
  'viet nam': 'vn',
  'vn': 'vn',
  // Hong Kong
  'hong kong': 'hk',
  'hk': 'hk',
  // Taiwan
  'taiwan': 'tw',
  'tw': 'tw',
  // Czech Republic
  'czech republic': 'cz',
  'czechia': 'cz',
  'cz': 'cz',
  // Greece
  'greece': 'gr',
  'gr': 'gr',
  // Hungary
  'hungary': 'hu',
  'hu': 'hu',
  // Romania
  'romania': 'ro',
  'ro': 'ro',
  // Bahrain
  'bahrain': 'bh',
  'bh': 'bh',
  // Kuwait
  'kuwait': 'kw',
  'kw': 'kw',
  // Oman
  'oman': 'om',
  'om': 'om',
}

const prospectCountry = computed(() => {
  return (contact.doc?.country || taskData.value?.country || '').trim()
})

const prospectCountryIso = computed(() => {
  const c = prospectCountry.value.toLowerCase()
  if (!c) return null
  if (countryToIsoMap[c]) return countryToIsoMap[c]
  if (c.length === 2 && /^[a-z]{2}$/.test(c)) return c
  return null
})

// Timezone and Dynamic Local Greeting
function resolveTimeZone(countryName, tzField) {
  const c = (countryName || '').toLowerCase()
  const t = (tzField || '').toLowerCase()

  if (t.includes('kolkata') || t.includes('+05:30') || t.includes('ist')) return 'Asia/Kolkata'
  if (t.includes('new_york') || t.includes('est') || t.includes('edt') || t.includes('-05:00')) return 'America/New_York'
  if (t.includes('vienna') || t.includes('cet') || t.includes('cest') || t.includes('+01:00')) return 'Europe/Vienna'
  if (t.includes('london') || t.includes('gmt') || t.includes('bst') || t.includes('+00:00')) return 'Europe/London'
  if (t.includes('berlin')) return 'Europe/Berlin'
  if (t.includes('paris')) return 'Europe/Paris'
  if (t.includes('dubai') || t.includes('+04:00')) return 'Asia/Dubai'
  if (t.includes('singapore') || t.includes('+08:00')) return 'Asia/Singapore'
  if (t.includes('sydney') || t.includes('+10:00') || t.includes('aest')) return 'Australia/Sydney'
  if (t.includes('zurich')) return 'Europe/Zurich'

  if (c === 'india' || c === 'in') return 'Asia/Kolkata'
  if (c === 'austria' || c === 'at') return 'Europe/Vienna'
  if (c === 'united states' || c === 'usa' || c === 'us') return 'America/New_York'
  if (c === 'united kingdom' || c === 'uk' || c === 'gb') return 'Europe/London'
  if (c === 'germany' || c === 'de') return 'Europe/Berlin'
  if (c === 'france' || c === 'fr') return 'Europe/Paris'
  if (c === 'australia' || c === 'au') return 'Australia/Sydney'
  if (c === 'uae' || c === 'united arab emirates' || c === 'ae') return 'Asia/Dubai'
  if (c === 'singapore' || c === 'sg') return 'Asia/Singapore'
  if (c === 'switzerland' || c === 'ch') return 'Europe/Zurich'
  if (c === 'canada' || c === 'ca') return 'America/Toronto'
  if (c === 'netherlands' || c === 'nl') return 'Europe/Amsterdam'
  if (c === 'ireland' || c === 'ie') return 'Europe/Dublin'

  if (tzField) {
    try {
      Intl.DateTimeFormat(undefined, { timeZone: tzField })
      return tzField
    } catch (e) {}
  }

  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata'
}

function getUtcOffset(timeZone, date) {
  try {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      timeZoneName: 'shortOffset',
    }).formatToParts(date)
    const tzPart = parts.find((p) => p.type === 'timeZoneName')
    if (tzPart?.value && tzPart.value.startsWith('GMT')) {
      const raw = tzPart.value.replace('GMT', 'UTC')
      const match = raw.match(/UTC([+-])(\d+)(?::(\d+))?/)
      if (match) {
        const sign = match[1]
        const h = match[2].padStart(2, '0')
        const m = (match[3] || '00').padStart(2, '0')
        return `UTC${sign}${h}:${m}`
      }
      return raw
    }
  } catch (e) {}

  if (timeZone === 'Asia/Kolkata') return 'UTC+05:30'
  if (timeZone === 'America/New_York' || timeZone === 'America/Toronto') return 'UTC-05:00'
  if (timeZone === 'Europe/Vienna' || timeZone === 'Europe/Berlin' || timeZone === 'Europe/Paris' || timeZone === 'Europe/Zurich' || timeZone === 'Europe/Amsterdam') return 'UTC+01:00'
  if (timeZone === 'Europe/London' || timeZone === 'Europe/Dublin') return 'UTC+00:00'
  if (timeZone === 'Asia/Dubai') return 'UTC+04:00'
  if (timeZone === 'Asia/Singapore') return 'UTC+08:00'
  if (timeZone === 'Australia/Sydney') return 'UTC+10:00'
  return 'UTC+05:30'
}

const resolvedTimeZone = computed(() => {
  return resolveTimeZone(prospectCountry.value, taskData.value?.timezone || contact.doc?.timezone)
})

const prospectTimezoneDisplay = computed(() => {
  const tz = resolvedTimeZone.value
  const offset = getUtcOffset(tz, currentTime.value)
  return `${tz} (${offset})`
})

const prospectLocalTime = computed(() => {
  const timeZone = resolvedTimeZone.value
  const now = currentTime.value

  try {
    const timeFormatter = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
    const timeFormatted = timeFormatter.format(now)

    const hourFormatter = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      hourCycle: 'h23',
    })
    const hour = parseInt(hourFormatter.format(now), 10)

    let greeting = 'Good morning'
    if (hour >= 5 && hour < 12) {
      greeting = 'Good morning'
    } else if (hour >= 12 && hour < 17) {
      greeting = 'Good afternoon'
    } else if (hour >= 17 && hour < 21) {
      greeting = 'Good evening'
    } else {
      greeting = 'Good night'
    }

    const offset = getUtcOffset(timeZone, now)

    return {
      time: timeFormatted,
      offset,
      greeting,
      display: `${timeFormatted} · ${offset} · ${greeting}`,
    }
  } catch (e) {
    return {
      time: '12:53 PM',
      offset: 'UTC+05:30',
      greeting: 'Good afternoon',
      display: '12:53 PM · UTC+05:30 · Good afternoon',
    }
  }
})

// Data Age & Last Updated
const dataAgeDisplay = computed(() => {
  if (!contact.doc?.creation) return '—'
  const diff = Date.now() - new Date(contact.doc.creation).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'Today'
  if (days === 1) return '1 day ago'
  return `${days} days ago`
})

const lastUpdatedDisplay = computed(() => {
  if (!contact.doc?.modified) return '—'
  try {
    const d = new Date(contact.doc.modified)
    const options = { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }
    return new Intl.DateTimeFormat('en-GB', options).format(d)
  } catch (e) {
    return contact.doc.modified
  }
})

// Colleagues list
const colleaguesList = ref([
  { name: 'c1', full_name: 'Jessica David', designation: 'VP - Sales' },
  { name: 'c2', full_name: 'Arun Raj', designation: 'CTO' },
  { name: 'c3', full_name: 'Priya Raman', designation: 'Marketing Manager' },
])

const colleagueColors = [
  'bg-purple-600',
  'bg-blue-600',
  'bg-emerald-600',
  'bg-amber-600',
  'bg-rose-600',
  'bg-indigo-600',
]

function getInitials(name) {
  if (!name) return 'SW'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

async function fetchColleagues() {
  const company = contact.doc?.company_name
  if (!company) return
  try {
    const res = await call('frappe.client.get_list', {
      doctype: 'Contact',
      filters: {
        company_name: company,
        name: ['!=', contact.doc.name],
      },
      fields: ['name', 'full_name', 'designation', 'mobile_no', 'email_id', 'image'],
      limit: 5,
    })
    if (res && res.length) {
      colleaguesList.value = res
    }
  } catch (e) {
    // Keep initial fallback sample
  }
}

// Social links modal
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

const rows = computed(() => [])
const columns = computed(() => [])

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
