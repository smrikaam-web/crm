<template>
  <!-- Full Call Window (Live Transcript + Call Notes) -->
  <div v-show="showCallPopup && !isDialPadRoute" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-50 flex flex-col rounded-2xl bg-[#18191e] text-ink-gray-2 shadow-2xl border border-surface-gray-7/80 transition-all duration-200 ease-out"
      :class="[
        isMaximized
          ? 'fixed inset-4 w-auto h-auto max-w-none max-h-none'
          : 'w-[780px] max-w-[95vw] h-[550px] max-h-[88vh]',
      ]"
      :style="isMaximized ? undefined : style"
    >
      <!-- Header / Drag Bar -->
      <div
        ref="dragHandle"
        class="flex items-center justify-between px-5 py-3 border-b border-surface-gray-7/50 select-none cursor-move"
      >
        <!-- Contact info & Status -->
        <div class="flex items-center gap-3">
          <Avatar
            v-if="contact?.image"
            :image="contact.image"
            :label="contact.full_name"
            class="relative flex !h-9 !w-9 items-center justify-center flex-shrink-0"
          />
          <div class="flex flex-col">
            <div class="text-base font-bold text-white leading-tight">
              {{ contact?.full_name || phoneNumber || __('Active Call') }}
            </div>
            <div class="text-xs text-ink-gray-4 leading-tight mt-0.5">
              {{ phoneNumber || contact?.mobile_no }}
            </div>
          </div>

          <!-- Connection Status Badge -->
          <div class="ml-2 flex items-center gap-2">
            <span
              v-if="onCall"
              class="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-400"
            >
              <span class="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {{ __('Connected') }}
            </span>
            <span
              v-else-if="calling || callStatus === 'initiating'"
              class="inline-flex items-center gap-1.5 rounded-full bg-blue-950/80 border border-blue-500/40 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-blue-400"
            >
              <span class="size-1.5 rounded-full bg-blue-400 animate-pulse" />
              {{ __('Calling...') }}
            </span>
            <span
              v-else-if="callStatus === 'ringing'"
              class="inline-flex items-center gap-1.5 rounded-full bg-amber-950/80 border border-amber-500/40 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-400"
            >
              <span class="size-1.5 rounded-full bg-amber-400 animate-pulse" />
              {{ __('Ringing...') }}
            </span>
            <span
              v-else-if="callStatus === 'failed'"
              class="inline-flex items-center gap-1.5 rounded-full bg-red-950/80 border border-red-500/40 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-red-400"
            >
              {{ __('Call Failed') }}
            </span>
            <span
              v-else-if="callStatus === 'disconnected' || callStatus === 'completed'"
              class="inline-flex items-center gap-1.5 rounded-full bg-surface-gray-8 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-ink-gray-4"
            >
              {{ __('Call Ended') }}
            </span>

            <!-- Duration Timer -->
            <CountUpTimer ref="counterUp">
              <span v-if="onCall" class="text-sm font-semibold text-white font-mono ml-1">
                {{ counterUp?.updatedTime || '00:00' }}
              </span>
            </CountUpTimer>
          </div>
        </div>

        <!-- Window Actions (Minimize, Maximize, Close) -->
        <div class="flex items-center gap-1 text-ink-gray-4" @mousedown.stop>
          <button
            type="button"
            class="p-1 rounded-md hover:bg-surface-gray-8 hover:text-white transition-colors"
            :title="__('Minimize')"
            @click="toggleCallWindow"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button
            type="button"
            class="p-1 rounded-md hover:bg-surface-gray-8 hover:text-white transition-colors"
            :title="isMaximized ? __('Restore') : __('Maximize')"
            @click="toggleMaximize"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="!isMaximized" d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
              <path v-else d="M4 14h6v6M20 10h-6V4M14 10l7-7M10 14l-7 7" />
            </svg>
          </button>
          <button
            type="button"
            class="p-1 rounded-md hover:bg-surface-gray-8 hover:text-white transition-colors"
            :title="__('Close')"
            @click="closeCallPopup"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Call Error Notice (if call failed) -->
      <div
        v-if="callStatus === 'failed'"
        class="mx-4 mt-3 flex items-center justify-between rounded-lg bg-red-950/60 border border-red-500/40 p-2.5 text-xs text-red-300"
      >
        <span>{{ callErrorMessage || __('Call could not be completed.') }}</span>
        <Button
          size="xs"
          variant="solid"
          theme="green"
          :label="__('Retry')"
          class="rounded text-ink-base"
          @click="retryCall"
        />
      </div>

      <!-- Main Body: 2 Side-by-Side Panels (Live Transcript & Call Notes) -->
      <div class="flex-1 grid grid-cols-2 gap-3 p-4 min-h-0 overflow-hidden">
        <!-- LEFT PANEL: Live Transcript -->
        <div class="flex flex-col rounded-xl bg-[#121316] border border-surface-gray-7/60 overflow-hidden min-h-0">
          <!-- Transcript Tabs & Controls Header -->
          <div class="flex items-center justify-between px-3 pt-2.5 pb-2 border-b border-surface-gray-7/40 bg-[#16171c]">
            <!-- Tab Pill -->
            <div class="flex items-center gap-1.5 rounded-lg bg-[#251e3e] border border-purple-500/60 px-3 py-1 text-xs font-semibold text-purple-200 shadow-sm">
              <span>{{ __('Live Transcript') }}</span>
            </div>

            <!-- Sub-actions: LIVE indicator & Font Sizing -->
            <div class="flex items-center gap-2">
              <div
                v-if="onCall"
                class="flex items-center gap-1 rounded bg-red-950/60 border border-red-500/30 px-2 py-0.5 text-[10px] font-bold text-red-400 tracking-wide"
              >
                <span class="size-1.5 rounded-full bg-red-500 animate-pulse" />
                <span>{{ __('LIVE') }}</span>
              </div>

              <!-- Font Size Toggle -->
              <div class="flex items-center rounded border border-surface-gray-7/60 bg-[#18191e] p-0.5 text-[11px] text-ink-gray-4">
                <button
                  type="button"
                  class="px-1.5 py-0.5 rounded transition-colors"
                  :class="{ 'bg-surface-gray-7 text-white font-semibold': transcriptFontSize === 'xs' }"
                  title="Smaller text"
                  @click="transcriptFontSize = 'xs'"
                >
                  A-
                </button>
                <button
                  type="button"
                  class="px-1.5 py-0.5 rounded transition-colors"
                  :class="{ 'bg-surface-gray-7 text-white font-semibold': transcriptFontSize === 'sm' }"
                  title="Default text"
                  @click="transcriptFontSize = 'sm'"
                >
                  A
                </button>
                <button
                  type="button"
                  class="px-1.5 py-0.5 rounded transition-colors"
                  :class="{ 'bg-surface-gray-7 text-white font-semibold': transcriptFontSize === 'base' }"
                  title="Larger text"
                  @click="transcriptFontSize = 'base'"
                >
                  A+
                </button>
              </div>
            </div>
          </div>

          <!-- Transcript Scrollable Stream -->
          <div
            ref="transcriptContainer"
            class="flex-1 overflow-y-auto p-3.5 flex flex-col gap-3 select-text scroll-smooth"
          >
            <!-- Empty States -->
            <div
              v-if="utterances.length === 0"
              class="flex flex-col items-center justify-center h-full text-center py-8 text-ink-gray-5"
            >
              <div v-if="transcriptionStatus === 'error' || transcriptionStatus === 'unavailable'" class="flex flex-col items-center gap-1.5 max-w-[260px]">
                <span class="size-2 rounded-full bg-amber-500" />
                <span class="text-xs font-medium text-ink-gray-4">
                  {{ __('Live transcription unavailable') }}
                </span>
                <span class="text-[11px] text-ink-gray-5">
                  {{ transcriptionError || __('Web Speech API or Twilio transcription stream is not active for this call.') }}
                </span>
              </div>
              <div v-else-if="transcriptionStatus === 'paused'" class="flex items-center gap-2 text-xs italic">
                <span class="size-2 rounded-full bg-amber-400" />
                <span>{{ __('Speech recognition paused (muted)') }}</span>
              </div>
              <div v-else class="flex flex-col items-center gap-2 text-xs italic">
                <div class="flex items-center gap-1.5">
                  <span class="size-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>{{ __('Listening for speech...') }}</span>
                </div>
                <span class="text-[11px] text-ink-gray-6 font-normal">
                  {{ __('Speech is automatically transcribed in real time.') }}
                </span>
              </div>
            </div>

            <!-- Utterance Items -->
            <div
              v-for="(item, index) in utterances"
              :key="index"
              class="flex items-start gap-2.5 text-left"
            >
              <!-- Timestamp (mm:ss) -->
              <span class="font-mono text-[11px] text-ink-gray-5 pt-0.5 w-10 flex-shrink-0">
                {{ formatSpeechTimestamp(item.timestamp) }}
              </span>

              <!-- Content (Speaker + Text) -->
              <div class="flex-1 flex flex-col gap-0.5">
                <div
                  class="text-xs font-semibold leading-tight"
                  :class="item.speaker === 'agent' ? 'text-sky-400' : 'text-emerald-400'"
                >
                  {{ getSpeakerDisplayName(item.speaker, contact?.full_name, currentUserName) }}
                </div>
                <div
                  class="text-ink-gray-2 leading-relaxed whitespace-pre-wrap break-words"
                  :class="[
                    transcriptFontSize === 'xs'
                      ? 'text-xs'
                      : transcriptFontSize === 'base'
                        ? 'text-base'
                        : 'text-sm',
                    { 'opacity-75 italic': !item.isFinal },
                  ]"
                >
                  {{ item.text }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT PANEL: Call Notes -->
        <div class="flex flex-col rounded-xl bg-[#121316] border border-surface-gray-7/60 overflow-hidden min-h-0">
          <!-- Notes Header + Formatting Toolbar -->
          <div class="flex items-center justify-between px-3 pt-2.5 pb-2 border-b border-surface-gray-7/40 bg-[#16171c]">
            <!-- Tab Pill -->
            <div class="flex items-center gap-1.5 rounded-lg bg-[#202127] border border-surface-gray-7/60 px-3 py-1 text-xs font-semibold text-ink-gray-2 shadow-sm">
              <span>{{ __('Call Notes') }}</span>
            </div>

            <!-- Formatting Toolbar -->
            <div class="flex items-center gap-1 text-ink-gray-4" @mousedown.stop>
              <button
                type="button"
                class="size-6 rounded hover:bg-surface-gray-7 hover:text-white font-bold text-xs flex items-center justify-center transition-colors"
                title="Bold"
                @click="applyFormatting('bold')"
              >
                B
              </button>
              <button
                type="button"
                class="size-6 rounded hover:bg-surface-gray-7 hover:text-white italic text-xs flex items-center justify-center transition-colors"
                title="Italic"
                @click="applyFormatting('italic')"
              >
                I
              </button>
              <button
                type="button"
                class="size-6 rounded hover:bg-surface-gray-7 hover:text-white underline text-xs flex items-center justify-center transition-colors"
                title="Underline"
                @click="applyFormatting('underline')"
              >
                U
              </button>
              <div class="h-3 w-px bg-surface-gray-7 mx-0.5" />
              <button
                type="button"
                class="size-6 rounded hover:bg-surface-gray-7 hover:text-white text-xs flex items-center justify-center transition-colors"
                title="Bullet list"
                @click="applyFormatting('bullet')"
              >
                •=
              </button>
              <button
                type="button"
                class="size-6 rounded hover:bg-surface-gray-7 hover:text-white text-xs flex items-center justify-center transition-colors font-mono"
                title="Numbered list"
                @click="applyFormatting('numbered')"
              >
                1.
              </button>
            </div>
          </div>

          <!-- Notes Textarea -->
          <div class="flex-1 flex flex-col p-3 min-h-0 bg-[#121316]">
            <textarea
              ref="notesTextarea"
              v-model="activeCallState.notes"
              class="flex-1 w-full bg-transparent text-sm text-ink-gray-2 placeholder:text-ink-gray-6 focus:outline-none resize-none leading-relaxed select-text cursor-text font-sans scroll-smooth"
              :placeholder="__('Type notes during call... (auto-saved)')"
              @input="handleNotesInput"
              @keydown.stop
              @mousedown.stop
              @click.stop
            />
          </div>

          <!-- Notes Footer: Auto-save status & Manual Save button -->
          <div class="flex items-center justify-between px-3 py-2 border-t border-surface-gray-7/40 bg-[#16171c] text-xs">
            <div class="flex items-center gap-1.5">
              <span v-if="isSavingNote" class="flex items-center gap-1.5 text-amber-400 font-normal">
                <span class="size-1.5 rounded-full bg-amber-400 animate-pulse" />
                <span>{{ __('Saving...') }}</span>
              </span>
              <span v-else-if="saveFailedNotice" class="flex items-center gap-1 text-red-400">
                <span>⚠</span>
                <span>{{ __('Save failed') }}</span>
              </span>
              <span v-else-if="lastSavedTime || noteSavedNotice" class="flex items-center gap-1 text-emerald-400 font-medium">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{{ __('Auto-saved at {0}', [lastSavedTime || counterUp?.updatedTime || '01:15 PM']) }}</span>
              </span>
              <span v-else class="text-ink-gray-5 text-[11px]">
                {{ __('Linked to prospect & call log') }}
              </span>
            </div>

            <Button
              size="xs"
              variant="subtle"
              :label="isSavingNote ? __('Saving...') : __('Save Note')"
              :loading="isSavingNote"
              class="text-[11px] h-6 px-2.5 rounded font-medium text-ink-base bg-surface-gray-7 hover:bg-surface-gray-6"
              @click="persistCallNote(true)"
            />
          </div>
        </div>
      </div>

      <!-- Dialpad Overlay Popover (when Keypad toggled) -->
      <div
        v-if="showKeypad"
        class="absolute bottom-20 left-16 z-50 rounded-xl bg-[#1c1d23] p-3 shadow-2xl border border-surface-gray-7/80 grid grid-cols-3 gap-2 w-48"
        @mousedown.stop
      >
        <button
          v-for="digit in keypadDigits"
          :key="digit"
          type="button"
          class="h-10 rounded-lg bg-surface-gray-8/90 hover:bg-surface-gray-7 text-white font-semibold text-base flex items-center justify-center transition-colors focus:outline-none"
          @click="sendDigit(digit)"
        >
          {{ digit }}
        </button>
      </div>

      <!-- Bottom Controls Bar -->
      <div class="flex items-center justify-between px-5 py-3 border-t border-surface-gray-7/60 bg-[#16171c] rounded-b-2xl select-none">
        <!-- Left Media Controls -->
        <div class="flex items-center gap-2.5">
          <!-- Mic / Mute -->
          <button
            type="button"
            class="size-10 rounded-full flex items-center justify-center transition-colors"
            :class="
              muted
                ? 'bg-red-950/80 text-red-400 border border-red-500/50 hover:bg-red-900/80'
                : 'bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-200'
            "
            :title="muted ? __('Unmute') : __('Mute')"
            @click="toggleMute"
          >
            <svg v-if="!muted" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
            <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
              <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </button>

          <!-- Keypad Toggle -->
          <button
            type="button"
            class="size-10 rounded-full flex items-center justify-center transition-colors"
            :class="showKeypad ? 'bg-surface-gray-6 text-white' : 'bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-200'"
            :title="__('Dialpad')"
            @click="toggleKeypad"
          >
            <DialpadIcon class="h-4 w-4" />
          </button>

          <!-- Hold / Pause -->
          <button
            type="button"
            class="size-10 rounded-full flex items-center justify-center transition-colors"
            :class="isHeld ? 'bg-amber-950/80 text-amber-400 border border-amber-500/50' : 'bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-200'"
            :title="isHeld ? __('Resume Call') : __('Hold Call')"
            @click="toggleHold"
          >
            <PauseIcon class="h-4 w-4" />
          </button>

          <!-- Volume / Speaker -->
          <button
            type="button"
            class="size-10 rounded-full flex items-center justify-center bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-200 transition-colors"
            :title="__('Speaker')"
            @click="toggleSpeaker"
          >
            <VolumnHighIcon class="h-4 w-4" />
          </button>

          <!-- Recording Indicator -->
          <div
            class="size-10 rounded-full flex items-center justify-center bg-surface-gray-8 text-red-500"
            :title="__('Call is being recorded')"
          >
            <span class="size-3 rounded-full bg-red-500 animate-pulse" />
          </div>
        </div>

        <!-- Right Call Actions -->
        <div>
          <!-- Connected: Red End Call Pill -->
          <div v-if="onCall">
            <button
              type="button"
              class="h-10 px-6 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg transition-colors cursor-pointer"
              @click="hangUpCall"
            >
              <PhoneIcon class="h-4 w-4 rotate-[135deg]" />
              <span>{{ __('End Call') }}</span>
            </button>
          </div>

          <!-- Initiating / Ringing: Cancel Button -->
          <div v-else-if="calling || callStatus === 'initiating' || callStatus === 'ringing'">
            <button
              type="button"
              class="h-10 px-5 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg transition-colors cursor-pointer"
              @click="cancelCall"
            >
              <PhoneIcon class="h-4 w-4 rotate-[135deg]" />
              <span>{{ __('Cancel') }}</span>
            </button>
          </div>

          <!-- Failed / Ended -->
          <div v-else-if="callStatus === 'failed' || callStatus === 'disconnected' || callStatus === 'cancelled'">
            <Button
              size="md"
              variant="subtle"
              :label="__('Close')"
              class="rounded-full text-ink-base"
              @click="closeCallPopup"
            />
          </div>

          <!-- Incoming: Accept / Reject Pills -->
          <div v-else class="flex items-center gap-2.5">
            <button
              type="button"
              class="h-10 px-6 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg transition-colors cursor-pointer"
              @click="acceptIncomingCall"
            >
              <PhoneIcon class="h-4 w-4" />
              <span>{{ __('Accept') }}</span>
            </button>
            <button
              type="button"
              class="h-10 px-6 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg transition-colors cursor-pointer"
              @click="rejectIncomingCall"
            >
              <PhoneIcon class="h-4 w-4 rotate-[135deg]" />
              <span>{{ __('Reject') }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Minimized Dock Widget (Bottom-Left Sidebar Card matching screenshot) -->
  <div
    v-show="showSmallCallWindow && !isDialPadRoute"
    class="fixed bottom-4 left-4 z-50 flex flex-col gap-2 rounded-xl bg-[#18191e] p-3 shadow-2xl border border-surface-gray-7/80 w-64 select-none cursor-pointer transition-transform hover:scale-[1.01]"
    v-bind="$attrs"
    @click="toggleCallWindow"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="size-2 rounded-full bg-emerald-500 animate-pulse" />
        <span class="text-xs font-semibold text-white uppercase tracking-wider">
          {{ onCall ? __('On Call') : calling ? __('Calling...') : __('Call') }}
        </span>
      </div>
      <div class="text-xs font-mono font-medium text-gray-300">
        {{ counterUp?.updatedTime || '00:00' }}
      </div>
    </div>
    <div class="text-xs text-gray-400 truncate">
      {{ contact?.full_name || phoneNumber || contact?.mobile_no }}
    </div>
    <div class="flex items-center justify-between pt-1" @click.stop>
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          class="size-7 rounded-full flex items-center justify-center bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-300"
          :class="{ 'bg-red-950 text-red-400': muted }"
          @click="toggleMute"
        >
          <svg v-if="!muted" class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          </svg>
          <svg v-else class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="1" y1="1" x2="23" y2="23" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
          </svg>
        </button>
        <button
          type="button"
          class="size-7 rounded-full flex items-center justify-center bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-300"
          @click="toggleKeypad"
        >
          <DialpadIcon class="size-3.5" />
        </button>
        <button
          type="button"
          class="size-7 rounded-full flex items-center justify-center bg-surface-gray-8 hover:bg-surface-gray-7 text-gray-300"
          :title="__('Restore Window')"
          @click="toggleCallWindow"
        >
          <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
          </svg>
        </button>
      </div>

      <button
        type="button"
        class="h-7 px-3 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium text-xs flex items-center gap-1.5 shadow"
        @click="hangUpCall"
      >
        <PhoneIcon class="size-3 rotate-[135deg]" />
        <span>{{ __('End Call') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import PauseIcon from '@/components/Icons/PauseIcon.vue'
import VolumnHighIcon from '@/components/Icons/VolumnHighIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { Device } from '@twilio/voice-sdk'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import {
  formatTranscriptUtterances,
  appendOrUpdateUtterance,
  formatSpeechTimestamp,
  getSpeakerDisplayName,
} from '@/utils/callTranscript'
import {
  validateTokenResponse,
  mapTwilioSignalingStatus,
  extractCallErrorMessage,
} from '@/utils/twilioCall'
import { Avatar, Button, call, createResource, toast } from 'frappe-ui'
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  activeCallState,
  registerTelephonyHandlers,
} from '@/composables/useTelephonyCall'

const route = useRoute()
const isDialPadRoute = computed(() => {
  const name = route?.name
  const path = route?.path || ''
  return (
    name === 'DialPad' ||
    path === '/calling/dialpad' ||
    path === '/dialpad' ||
    path.startsWith('/calling/dialpad') ||
    path.startsWith('/dialpad')
  )
})

const { capture } = useTelemetry()
const { $socket } = globalStore()
const users = usersStore()
const session = sessionStore()

const currentUserName = computed(() => {
  return users.getUser(session.user)?.full_name || session.user || 'Sam Walker'
})

let device = null
let log = ref('Connecting...')
let _call = null

const showCallPopup = ref(false)
const showSmallCallWindow = ref(false)
const isMaximized = ref(false)
const onCall = ref(false)
const calling = ref(false)
const muted = ref(false)
const isHeld = ref(false)
const showKeypad = ref(false)
const callPopup = ref(null)
const dragHandle = ref(null)
const counterUp = ref(null)
const callStatus = ref('')
const notesTextarea = ref(null)
const transcriptFontSize = ref('sm') // 'xs' | 'sm' | 'base'

const deviceStatus = ref('uninitialized')
const deviceErrorMessage = ref('')
const callErrorMessage = ref('')
let isCallPendingConnect = false
let closeStatusTimer = null

const activeCallSid = ref('')
const utterances = ref([])
const transcriptionStatus = ref('idle') // 'idle' | 'listening' | 'transcribing' | 'paused' | 'unavailable' | 'error'
const transcriptionError = ref('')
const transcriptContainer = ref(null)
let transcriptSaved = false

// Speech Recognition instance
let speechRecognizer = null
let speechRecognitionActive = false

const keypadDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']
const phoneNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

// Call Notes Auto-Save & Manual Save
const isSavingNote = ref(false)
const noteSavedNotice = ref(false)
const saveFailedNotice = ref(false)
const lastSavedTime = ref('')
let notesDebounceTimer = null

function handleNotesInput() {
  activeCallState.saveStatus = 'saving'
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  notesDebounceTimer = setTimeout(() => {
    persistCallNote(false)
  }, 1200)
}

async function persistCallNote(isExplicit = false) {
  const content = (activeCallState.notes || '').trim()
  const sid = activeCallSid.value || _call?.parameters?.CallSid || activeCallState.activeCallSid
  if (!content && !activeCallState.noteDocName) {
    return
  }
  if (!sid) {
    return
  }

  isSavingNote.value = true
  saveFailedNotice.value = false
  try {
    const res = await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: sid,
      note: {
        name: activeCallState.noteDocName || undefined,
        title: __('Call Note') + (contact.value?.full_name ? ` - ${contact.value.full_name}` : ''),
        content: activeCallState.notes,
      },
    })
    if (res?.name) {
      activeCallState.noteDocName = res.name
    }
    const now = new Date()
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })
    lastSavedTime.value = timeStr
    activeCallState.lastSavedTime = timeStr
    activeCallState.saveStatus = 'saved'
    noteSavedNotice.value = true
    setTimeout(() => {
      noteSavedNotice.value = false
    }, 2500)
    if (isExplicit) {
      toast.success(__('Call note saved'))
    }
    capture('note_updated')
  } catch (err) {
    console.error('Failed to save in-call note:', err)
    saveFailedNotice.value = true
    activeCallState.saveStatus = 'failed'
    if (isExplicit) {
      toast.error(__('Failed to save note'))
    }
  } finally {
    isSavingNote.value = false
  }
}

// Formatting toolbar helpers for Call Notes textarea
function applyFormatting(type) {
  const textarea = notesTextarea.value
  if (!textarea) return
  const start = textarea.selectionStart ?? 0
  const end = textarea.selectionEnd ?? 0
  const text = activeCallState.notes || ''
  const selectedText = text.substring(start, end)
  let replacement = ''
  let newCursorPos = start

  if (type === 'bold') {
    replacement = selectedText ? `**${selectedText}**` : '**'
    newCursorPos = selectedText ? start + replacement.length : start + 2
  } else if (type === 'italic') {
    replacement = selectedText ? `*${selectedText}*` : '*'
    newCursorPos = selectedText ? start + replacement.length : start + 1
  } else if (type === 'underline') {
    replacement = selectedText ? `<u>${selectedText}</u>` : '<u></u>'
    newCursorPos = selectedText ? start + replacement.length : start + 3
  } else if (type === 'bullet') {
    const lines = selectedText ? selectedText.split('\n') : ['']
    replacement = lines.map((l) => (l.startsWith('• ') || l.startsWith('- ') ? l : `• ${l}`)).join('\n')
    newCursorPos = start + replacement.length
  } else if (type === 'numbered') {
    const lines = selectedText ? selectedText.split('\n') : ['']
    replacement = lines.map((l, i) => (l.match(/^\d+\.\s/) ? l : `${i + 1}. ${l}`)).join('\n')
    newCursorPos = start + replacement.length
  }

  activeCallState.notes = text.substring(0, start) + replacement + text.substring(end)
  handleNotesInput()

  nextTick(() => {
    textarea.focus()
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  })
}

// Draggable positioning with handle & preventDefault=false
const { width, height } = useWindowSize()
const { style } = useDraggable(callPopup, {
  handle: dragHandle,
  initialValue: { x: Math.max(20, width.value - 820), y: Math.max(20, height.value - 600) },
  preventDefault: false,
})

function toggleMaximize() {
  isMaximized.value = !isMaximized.value
  activeCallState.isMaximized = isMaximized.value
}

// Web Speech Recognition for Real Live Voice-to-Text
function initSpeechRecognition() {
  const SpeechRecognitionClass =
    typeof window !== 'undefined'
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null

  if (!SpeechRecognitionClass) {
    if (transcriptionStatus.value === 'idle') {
      transcriptionStatus.value = 'unavailable'
      activeCallState.transcriptionStatus = 'unavailable'
      transcriptionError.value = __('Your browser does not support the Web Speech Recognition API.')
    }
    return
  }

  try {
    speechRecognizer = new SpeechRecognitionClass()
    speechRecognizer.continuous = true
    speechRecognizer.interimResults = true
    speechRecognizer.lang = navigator.language || 'en-US'

    speechRecognizer.onstart = () => {
      speechRecognitionActive = true
      transcriptionStatus.value = 'listening'
      activeCallState.transcriptionStatus = 'listening'
      transcriptionError.value = ''
    }

    speechRecognizer.onresult = (event) => {
      if (!onCall.value) return
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i]
        const text = item[0]?.transcript || ''
        if (item.isFinal) {
          finalTranscript += text
        } else {
          interimTranscript += text
        }
      }

      const agentTimestamp = counterUp.value?.updatedTime || '00:00'

      if (finalTranscript.trim()) {
        transcriptionStatus.value = 'transcribing'
        activeCallState.transcriptionStatus = 'transcribing'
        utterances.value = appendOrUpdateUtterance(utterances.value, {
          speaker: 'agent',
          text: finalTranscript.trim(),
          isFinal: true,
          timestamp: agentTimestamp,
        })
        activeCallState.utterances = utterances.value
        scrollToBottom()
      } else if (interimTranscript.trim()) {
        transcriptionStatus.value = 'transcribing'
        activeCallState.transcriptionStatus = 'transcribing'
        utterances.value = appendOrUpdateUtterance(utterances.value, {
          speaker: 'agent',
          text: interimTranscript.trim(),
          isFinal: false,
          timestamp: agentTimestamp,
        })
        activeCallState.utterances = utterances.value
        scrollToBottom()
      }
    }

    speechRecognizer.onerror = (event) => {
      console.warn('Speech recognition event error:', event.error)
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        transcriptionStatus.value = 'unavailable'
        activeCallState.transcriptionStatus = 'unavailable'
        transcriptionError.value = __('Microphone access denied for live speech recognition.')
      }
    }

    speechRecognizer.onend = () => {
      speechRecognitionActive = false
      if (onCall.value && !muted.value && transcriptionStatus.value !== 'unavailable') {
        try {
          speechRecognizer.start()
        } catch (e) {
          console.warn('Could not restart speech recognition:', e)
        }
      } else if (muted.value && onCall.value) {
        transcriptionStatus.value = 'paused'
        activeCallState.transcriptionStatus = 'paused'
      }
    }
  } catch (err) {
    console.warn('Failed to construct SpeechRecognition:', err)
    transcriptionStatus.value = 'unavailable'
    activeCallState.transcriptionStatus = 'unavailable'
    transcriptionError.value = err.message || __('Speech recognition initialization failed.')
  }
}

function startSpeechRecognition() {
  if (!speechRecognizer) {
    initSpeechRecognition()
  }
  if (speechRecognizer && !speechRecognitionActive) {
    try {
      speechRecognizer.start()
    } catch (e) {
      console.warn('Speech recognition start failed:', e)
    }
  }
}

function stopSpeechRecognition() {
  if (speechRecognizer && speechRecognitionActive) {
    try {
      speechRecognizer.stop()
    } catch (e) {}
    speechRecognitionActive = false
  }
  if (transcriptionStatus.value !== 'unavailable') {
    transcriptionStatus.value = 'idle'
    activeCallState.transcriptionStatus = 'idle'
  }
}

// Twilio Live Transcription Socket Event Handler
function handleLiveTranscriptEvent(data) {
  if (!data || !data.text) return

  if (activeCallSid.value && data.call_sid && data.call_sid !== activeCallSid.value) {
    return
  }
  if (!activeCallSid.value && data.call_sid) {
    activeCallSid.value = data.call_sid
  }

  transcriptionStatus.value = 'listening'
  activeCallState.transcriptionStatus = 'listening'

  utterances.value = appendOrUpdateUtterance(utterances.value, {
    speaker: data.speaker,
    text: data.text,
    isFinal: data.is_final,
    timestamp: data.timestamp || counterUp.value?.updatedTime || '00:00',
  })
  activeCallState.utterances = utterances.value

  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (transcriptContainer.value) {
      transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
    }
  })
}

async function saveFinalTranscript() {
  if (transcriptSaved) return
  const sid = activeCallSid.value || _call?.parameters?.CallSid
  if (!sid || utterances.value.length === 0) return

  transcriptSaved = true
  const formatted = formatTranscriptUtterances(utterances.value)

  try {
    await call('crm.integrations.twilio.api.save_call_transcript', {
      call_sid: sid,
      transcript: formatted,
    })
  } catch (err) {
    console.error('Failed to save call transcript to CRM:', err)
  }
}

function resetTranscriptState() {
  utterances.value = []
  activeCallState.utterances = []
  activeCallSid.value = ''
  transcriptionStatus.value = 'idle'
  activeCallState.transcriptionStatus = 'idle'
  transcriptionError.value = ''
  transcriptSaved = false
}

function handleSocketMessage(data) {
  if (!data) return
  if (data.event === 'started') {
    transcriptionStatus.value = 'listening'
    activeCallState.transcriptionStatus = 'listening'
    return
  }
  if (data.event === 'stopped') {
    return
  }
  if (data.event === 'content') {
    handleLiveTranscriptEvent(data)
  }
}

function setupSocket() {
  if ($socket) {
    $socket.on('twilio_transcription', handleSocketMessage)
  }
}

onMounted(() => {
  setupSocket()
  initSpeechRecognition()
})

onBeforeUnmount(() => {
  stopSpeechRecognition()
  if ($socket) {
    $socket.off('twilio_transcription', handleSocketMessage)
  }
})

// Twilio Telephony Setup
async function startupClient() {
  if (deviceStatus.value === 'initializing' || deviceStatus.value === 'registering') {
    return false
  }

  deviceStatus.value = 'initializing'
  deviceErrorMessage.value = ''
  log.value = 'Requesting Access Token...'

  try {
    setupSocket()
    const data = await call('crm.integrations.twilio.api.generate_access_token')

    const validation = validateTokenResponse(data)
    if (!validation.ok) {
      const msg = __(validation.message)
      deviceStatus.value = 'error'
      deviceErrorMessage.value = msg
      log.value = msg
      return false
    }

    log.value = 'Got a token.'
    intitializeDevice(validation.token)
    return true
  } catch (err) {
    const msg =
      err.messages?.[0] ||
      err.message ||
      __('An error occurred while requesting Twilio access token.')
    deviceStatus.value = 'error'
    deviceErrorMessage.value = msg
    log.value = msg
    return false
  }
}

function intitializeDevice(token) {
  if (!token) {
    deviceStatus.value = 'error'
    deviceErrorMessage.value = __('Invalid Twilio token received.')
    log.value = deviceErrorMessage.value
    return
  }

  try {
    if (device && typeof device.destroy === 'function') {
      try {
        device.destroy()
      } catch (e) {
        console.warn('Error destroying existing device instance:', e)
      }
    }

    device = new Device(token, {
      codecPreferences: ['opus', 'pcmu'],
      fakeLocalDTMF: true,
      enableRingingState: true,
    })

    addDeviceListeners()
    deviceStatus.value = 'registering'
    device.register()
  } catch (err) {
    deviceStatus.value = 'error'
    deviceErrorMessage.value =
      err.message || __('Failed to initialize Twilio device.')
    log.value = deviceErrorMessage.value
  }
}

function addDeviceListeners() {
  if (!device) return

  device.on('registered', () => {
    deviceStatus.value = 'ready'
    deviceErrorMessage.value = ''
    log.value = 'Ready to make and receive calls!'
  })

  device.on('registering', () => {
    deviceStatus.value = 'registering'
    log.value = 'Registering Twilio device...'
  })

  device.on('unregistered', () => {
    deviceStatus.value = 'unregistered'
    log.value = 'Twilio device unregistered'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + (error.message || error)
    let userMsg = error.message || __('Twilio connection error')
    if (error.code === 31204 || error.code === 31205) {
      userMsg = __('Twilio authentication expired. Please refresh.')
    }
    deviceErrorMessage.value = userMsg

    if (calling.value && !onCall.value) {
      callStatus.value = 'failed'
      calling.value = false
      callErrorMessage.value = userMsg
    }
    if (!onCall.value && !calling.value) {
      deviceStatus.value = 'error'
    }
  })

  device.on('incoming', handleIncomingCall)

  device.on('tokenWillExpire', async () => {
    try {
      const data = await call('crm.integrations.twilio.api.generate_access_token')
      if (data?.token && device) {
        device.updateToken(data.token)
      }
    } catch (e) {
      console.error('Failed to refresh Twilio token:', e)
    }
  })
}

function waitForDeviceRegistered(timeoutMs = 6000) {
  return new Promise((resolve) => {
    if (device?.state === 'registered' || deviceStatus.value === 'ready') {
      return resolve(true)
    }

    let timer = null
    const onRegistered = () => {
      cleanup()
      resolve(true)
    }
    const onError = () => {
      cleanup()
      resolve(false)
    }
    const cleanup = () => {
      if (timer) clearTimeout(timer)
      device?.removeListener('registered', onRegistered)
      device?.removeListener('error', onError)
    }

    timer = setTimeout(() => {
      cleanup()
      resolve(device?.state === 'registered' || deviceStatus.value === 'ready')
    }, timeoutMs)

    device?.once('registered', onRegistered)
    device?.once('error', onError)
  })
}

function toggleMute() {
  if (!_call) return
  if (_call.isMuted()) {
    _call.mute(false)
    muted.value = false
    activeCallState.muted = false
    if (onCall.value) {
      startSpeechRecognition()
    }
  } else {
    _call.mute(true)
    muted.value = true
    activeCallState.muted = true
    if (speechRecognizer && speechRecognitionActive) {
      stopSpeechRecognition()
      transcriptionStatus.value = 'paused'
      activeCallState.transcriptionStatus = 'paused'
    }
  }
}

function toggleHold() {
  if (!_call) return
  isHeld.value = !isHeld.value
  if (isHeld.value) {
    _call.mute(true)
    if (speechRecognizer && speechRecognitionActive) {
      stopSpeechRecognition()
      transcriptionStatus.value = 'paused'
      activeCallState.transcriptionStatus = 'paused'
    }
  } else if (!muted.value) {
    _call.mute(false)
    if (onCall.value) {
      startSpeechRecognition()
    }
  }
}

function toggleSpeaker() {
  toast.info(__('Speaker audio device active'))
}

function toggleKeypad() {
  showKeypad.value = !showKeypad.value
}

function sendDigit(digit) {
  if (_call && onCall.value) {
    _call.sendDigits(digit)
  }
}

function handleIncomingCall(call) {
  resetTranscriptState()
  log.value = `Incoming call from ${call.parameters.From}`
  phoneNumber.value = call.parameters.From

  showCallPopup.value = true
  showSmallCallWindow.value = false
  _call = call
  if (call.parameters?.CallSid) {
    activeCallSid.value = call.parameters.CallSid
  }

  _call.on('accept', () => {
    if (_call?.parameters?.CallSid) {
      activeCallSid.value = _call.parameters.CallSid
    }
  })

  call.on('cancel', handleDisconnectedIncomingCall)
  call.on('disconnect', handleDisconnectedIncomingCall)
  call.on('reject', handleDisconnectedIncomingCall)
}

async function acceptIncomingCall() {
  log.value = 'Accepted incoming call.'
  onCall.value = true
  callStatus.value = 'connected'
  if (_call?.parameters?.CallSid) {
    activeCallSid.value = _call.parameters.CallSid
  }
  await _call.accept()
  counterUp.value?.start()
  startSpeechRecognition()
}

function rejectIncomingCall() {
  if (_call) {
    try {
      _call.reject()
    } catch (e) {}
  }
  log.value = 'Rejected incoming call'
  closeCallPopup()
}

async function hangUpCall() {
  stopSpeechRecognition()
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  log.value = 'Hanging up call'
  if (_call) {
    try {
      _call.disconnect()
    } catch (e) {
      console.warn('Error disconnecting on hangup:', e)
    }
  }
  handleCallDisconnected()
}

async function handleDisconnectedIncomingCall() {
  stopSpeechRecognition()
  log.value = `Call ended from handle disconnected Incoming call.`
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  closeCallPopup()
}

async function makeOutgoingCall(number) {
  if (!number) {
    toast.error(__('Please enter a valid phone number to call.'))
    return
  }

  if (onCall.value || calling.value || callStatus.value === 'initiating' || isCallPendingConnect) {
    toast.warning(__('A call is already in progress.'))
    return
  }

  if (closeStatusTimer) {
    clearTimeout(closeStatusTimer)
    closeStatusTimer = null
  }

  isCallPendingConnect = true
  phoneNumber.value = number
  resetTranscriptState()

  showCallPopup.value = true
  showSmallCallWindow.value = false
  callStatus.value = 'initiating'
  calling.value = true
  onCall.value = false
  muted.value = false
  isHeld.value = false
  showKeypad.value = false
  callErrorMessage.value = ''

  try {
    if (!device || deviceStatus.value !== 'ready') {
      log.value = 'Twilio device not ready. Initializing...'
      const ok = await startupClient()
      if (!ok || !device) {
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value =
          deviceErrorMessage.value ||
          __(
            'Twilio telephony service is not ready. Please verify your phone mapping and settings.',
          )
        return
      }

      if (device.state !== 'registered') {
        await waitForDeviceRegistered(6000)
      }

      if (deviceStatus.value === 'error') {
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value =
          deviceErrorMessage.value || __('Twilio registration failed.')
        return
      }
    }

    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      return
    }

    if (navigator?.mediaDevices?.getUserMedia) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true })
      } catch (micErr) {
        console.warn('Microphone permission check failed:', micErr)
        callStatus.value = 'failed'
        calling.value = false
        callErrorMessage.value = __(
          'Microphone permission denied. Please allow microphone access in your browser to place calls.',
        )
        return
      }
    }

    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      return
    }

    log.value = `Attempting to call ${number} ...`
    callStatus.value = 'initiating'

    const callParams = { To: number }
    if (activeCallState.callerId) {
      callParams.callerId = activeCallState.callerId
      callParams.From = activeCallState.callerId
    }

    _call = await device.connect({
      params: callParams,
    })

    if (_call?.parameters?.CallSid) {
      activeCallSid.value = _call.parameters.CallSid
    }

    if (callStatus.value === 'cancelled' || !showCallPopup.value) {
      if (_call) {
        try {
          _call.disconnect()
        } catch (e) {}
        _call = null
      }
      return
    }

    capture('make_outgoing_call')
    attachOutgoingCallListeners(_call)
  } catch (error) {
    console.error('Error during makeOutgoingCall:', error)
    log.value = `Could not connect call: ${error.message}`
    callStatus.value = 'failed'
    calling.value = false
    transcriptionStatus.value = 'error'
    callErrorMessage.value = __(extractCallErrorMessage(error))
  } finally {
    isCallPendingConnect = false
  }
}

function attachOutgoingCallListeners(callInstance) {
  if (!callInstance) return

  callInstance.on('ringing', () => {
    log.value = 'Ringing...'
    if (!onCall.value) {
      callStatus.value = 'ringing'
      activeCallState.status = 'ringing'
    }
  })

  callInstance.on('messageReceived', (message) => {
    let info = message?.content
    if (typeof info === 'string') {
      try {
        info = JSON.parse(info)
      } catch (e) {}
    }
    if (!info) return

    const rawStatus = info.CallStatus || info.call_status || info.status
    const signalingStatus = mapTwilioSignalingStatus(rawStatus)
    if (info.ParentCallSid) {
      activeCallSid.value = info.ParentCallSid
    } else if (info.CallSid && !activeCallSid.value) {
      activeCallSid.value = info.CallSid
    }

    log.value = `Call status update: ${rawStatus}`

    if (signalingStatus === 'ringing') {
      if (!onCall.value) {
        callStatus.value = 'ringing'
      }
    } else if (signalingStatus === 'connected') {
      log.value = 'Call in progress (answered).'
      callStatus.value = 'connected'
      calling.value = false
      onCall.value = true
      counterUp.value?.start()
      startSpeechRecognition()
    } else if (
      signalingStatus === 'busy' ||
      signalingStatus === 'no-answer' ||
      signalingStatus === 'failed'
    ) {
      log.value = `Call not completed: ${rawStatus}`
      callStatus.value = 'failed'
      calling.value = false
      onCall.value = false
      counterUp.value?.stop()
      callErrorMessage.value =
        signalingStatus === 'busy'
          ? __('Line is busy.')
          : signalingStatus === 'no-answer'
            ? __('No answer from recipient.')
            : __('Call failed to connect.')
    } else if (signalingStatus === 'completed') {
      handleCallDisconnected()
    }
  })

  callInstance.on('accept', () => {
    log.value = 'Call stream accepted by Twilio'
    if (callInstance?.parameters?.CallSid) {
      activeCallSid.value = callInstance.parameters.CallSid
    }
    onCall.value = true
    calling.value = false
    callStatus.value = 'connected'
    activeCallState.onCall = true
    activeCallState.calling = false
    activeCallState.status = 'connected'
    counterUp.value?.start()
    startSpeechRecognition()
  })

  callInstance.on('disconnect', () => {
    handleCallDisconnected()
  })

  callInstance.on('cancel', () => {
    log.value = 'Call cancelled'
    handleCallCancelled()
  })

  callInstance.on('error', (err) => {
    console.error('Twilio Call Error:', err)
    log.value = 'Call error: ' + (err.message || err)
    callStatus.value = 'failed'
    calling.value = false
    onCall.value = false
    callErrorMessage.value = err.message || __('Call encountered an error.')
    counterUp.value?.stop()
  })
}

async function handleCallDisconnected() {
  log.value = 'Call ended (disconnected).'
  stopSpeechRecognition()
  if (notesDebounceTimer) clearTimeout(notesDebounceTimer)
  await persistCallNote(false)
  await saveFinalTranscript()
  callStatus.value = 'disconnected'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'disconnected'
  activeCallState.calling = false
  activeCallState.onCall = false
  counterUp.value?.stop()
  muted.value = false
  isHeld.value = false
  showKeypad.value = false

  if (closeStatusTimer) clearTimeout(closeStatusTimer)
  closeStatusTimer = setTimeout(() => {
    if (callStatus.value === 'disconnected') {
      closeCallPopup()
    }
  }, 2000)
}

function handleCallCancelled() {
  log.value = 'Call cancelled'
  stopSpeechRecognition()
  callStatus.value = 'cancelled'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'cancelled'
  activeCallState.calling = false
  activeCallState.onCall = false
  counterUp.value?.stop()
  muted.value = false
  isHeld.value = false
  showKeypad.value = false

  if (closeStatusTimer) clearTimeout(closeStatusTimer)
  closeStatusTimer = setTimeout(() => {
    if (callStatus.value === 'cancelled') {
      closeCallPopup()
    }
  }, 1200)
}

function cancelCall() {
  log.value = 'User clicked Cancel.'
  stopSpeechRecognition()
  callStatus.value = 'cancelled'
  calling.value = false
  onCall.value = false
  activeCallState.status = 'cancelled'
  activeCallState.calling = false
  activeCallState.onCall = false

  if (_call) {
    try {
      _call.disconnect()
    } catch (e) {
      console.warn('Error disconnecting call on cancel:', e)
    }
    _call = null
  }

  counterUp.value?.stop()
  resetTranscriptState()
  closeCallPopup()
}

function retryCall() {
  callStatus.value = ''
  callErrorMessage.value = ''
  if (phoneNumber.value) {
    makeOutgoingCall(phoneNumber.value)
  }
}

function closeCallPopup() {
  stopSpeechRecognition()
  if (closeStatusTimer) {
    clearTimeout(closeStatusTimer)
    closeStatusTimer = null
  }
  showCallPopup.value = false
  showSmallCallWindow.value = false
  showKeypad.value = false
  isSavingNote.value = false
  noteSavedNotice.value = false
  saveFailedNotice.value = false
  isHeld.value = false
  if (notesDebounceTimer) {
    clearTimeout(notesDebounceTimer)
    notesDebounceTimer = null
  }
  callStatus.value = ''
  callErrorMessage.value = ''
  calling.value = false
  onCall.value = false
  muted.value = false
  activeCallState.status = 'idle'
  activeCallState.onCall = false
  activeCallState.calling = false
  activeCallState.duration = '00:00:00'
  _call = null
  resetTranscriptState()
}

function isCallInProgress() {
  return Boolean(
    onCall.value ||
    calling.value ||
    callStatus.value === 'initiating' ||
    callStatus.value === 'ringing' ||
    isCallPendingConnect,
  )
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
  activeCallState.isMinimized = showSmallCallWindow.value
}

watch(onCall, (value) => {
  if (!value) {
    showKeypad.value = false
  }
})

// Sync internal telephony state to shared activeCallState
watch(callStatus, (val) => {
  activeCallState.status = val || (onCall.value ? 'connected' : calling.value ? 'initiating' : 'idle')
})
watch(onCall, (val) => {
  activeCallState.onCall = val
  if (!val) {
    activeCallState.duration = '00:00:00'
  }
})
watch(calling, (val) => {
  activeCallState.calling = val
})
watch(phoneNumber, (val) => {
  activeCallState.phoneNumber = val || ''
})
watch(
  contact,
  (val) => {
    if (val) {
      activeCallState.contact = {
        full_name: val.full_name || activeCallState.contact.full_name || '',
        image: val.image || activeCallState.contact.image || '',
        mobile_no: val.mobile_no || activeCallState.contact.mobile_no || '',
        organization: val.company_name || val.organization || activeCallState.contact.organization || '',
        designation: val.designation || activeCallState.contact.designation || '',
      }
    }
  },
  { deep: true },
)
watch(muted, (val) => {
  activeCallState.muted = val
})
watch(activeCallSid, (val) => {
  activeCallState.activeCallSid = val
})
watch(callErrorMessage, (val) => {
  activeCallState.errorMessage = val
})

let durationSyncTimer = null
onMounted(() => {
  durationSyncTimer = setInterval(() => {
    if (onCall.value && counterUp.value?.updatedTime) {
      activeCallState.duration = counterUp.value.updatedTime
    }
  }, 500)

  registerTelephonyHandlers({
    makeCall: (num, contactData) => {
      if (contactData) {
        activeCallState.contact = {
          full_name: contactData.full_name || contactData.name || '',
          image: contactData.image || '',
          organization: contactData.organization || contactData.company || '',
          designation: contactData.designation || '',
          mobile_no: num,
        }
      }
      makeOutgoingCall(num)
    },
    hangupCall: () => hangUpCall(),
    cancelCall: () => cancelCall(),
    toggleMute: () => toggleMute(),
    sendDigit: (d) => sendDigit(d),
    saveNote: (content) => {
      activeCallState.notes = content
      handleNotesInput()
    },
    openCallWindow: () => {
      showCallPopup.value = true
      showSmallCallWindow.value = false
      activeCallState.isMinimized = false
    },
    minimizeCallWindow: () => {
      showCallPopup.value = false
      showSmallCallWindow.value = true
      activeCallState.isMinimized = true
    },
  })
})

onBeforeUnmount(() => {
  if (durationSyncTimer) {
    clearInterval(durationSyncTimer)
  }
})

defineExpose({
  makeOutgoingCall,
  setup: startupClient,
  isCallInProgress,
  closeCallPopup,
  toggleCallWindow,
})
</script>
