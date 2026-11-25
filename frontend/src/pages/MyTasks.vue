<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Header -->
    <header class="relative z-30 flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-6 py-3.5 dark:border-outline-gray-7">
      <div class="flex items-center gap-3">
        <div class="flex size-8 items-center justify-center rounded bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3">
          <TaskIcon class="size-4.5" />
        </div>
        <div>
          <h1 class="text-lg font-semibold text-ink-gray-9 dark:text-ink-white">
            {{ __('My Tasks') }}
          </h1>
          <p class="text-xs text-ink-gray-5">
            {{ __('Manage and execute your daily allocated prospect outreach') }}
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <!-- 1. All Users Dropdown Button (Matching Reference Image) -->
        <Dropdown v-if="isAdmin" :options="userDropdownOptions">
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs font-semibold text-ink-gray-8 shadow-2xs hover:bg-surface-gray-2 dark:border-outline-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2"
          >
            <LucideUsers class="size-3.5 text-ink-gray-5" />
            <span>{{ selectedUserLabel }}</span>
            <span class="lucide-chevron-down size-3 text-ink-gray-4" />
          </button>
        </Dropdown>
        <div
          v-else
          class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs font-semibold text-ink-gray-8 shadow-2xs dark:border-outline-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2"
        >
          <LucideUser class="size-3.5 text-ink-gray-5" />
          <span>{{ currentUserName || __('My Tasks') }}</span>
        </div>

        <!-- 2. Filter Button with 6-category flyout submenu -->
        <div ref="filterDropdownContainerRef" class="relative z-50">
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs font-semibold text-ink-gray-8 shadow-2xs transition-colors hover:bg-surface-gray-2 dark:border-outline-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2"
            :class="totalActiveFiltersCount > 0 ? 'border-primary-500 text-primary-600 bg-primary-50/50 dark:bg-primary-950/20' : ''"
            @click="showFilterMenu = !showFilterMenu"
          >
            <LucideFilter class="size-3.5" :class="totalActiveFiltersCount > 0 ? 'text-primary-600' : 'text-ink-gray-5'" />
            <span>{{ __('Filter') }}</span>
            <Badge
              v-if="totalActiveFiltersCount > 0"
              variant="solid"
              size="sm"
              class="h-4 min-w-[16px] px-1 text-[10px]"
            >
              {{ totalActiveFiltersCount }}
            </Badge>
            <span class="lucide-chevron-down size-3 text-ink-gray-4" />
          </button>

          <!-- 6-Category Unified Dropdown Panel (Completely solid, zero overlap, high z-index) -->
          <div
            v-if="showFilterMenu"
            class="absolute right-0 top-full z-[100] mt-2 flex flex-col w-[480px] max-w-[calc(100vw-32px)] rounded-xl border border-outline-gray-3 !bg-white shadow-2xl dark:border-outline-gray-6 dark:!bg-[#1e293b] overflow-hidden"
            @click.stop
          >
            <!-- Dropdown Header -->
            <div class="flex items-center justify-between px-3.5 py-2.5 border-b border-outline-gray-2 dark:border-outline-gray-7 !bg-[#f1f5f9] dark:!bg-[#0f172a]">
              <div class="flex items-center gap-1.5 text-xs font-bold text-ink-gray-9 dark:text-ink-white">
                <LucideFilter class="size-3.5 text-ink-gray-5" />
                <span>{{ __('Filter Tasks') }}</span>
                <Badge v-if="totalActiveFiltersCount > 0" variant="solid" size="sm" class="ml-1">
                  {{ totalActiveFiltersCount }} {{ __('active') }}
                </Badge>
              </div>
              <button
                v-if="totalActiveFiltersCount > 0"
                type="button"
                class="text-[11px] font-semibold text-surface-red-5 hover:underline cursor-pointer"
                @click="clearAllFilters"
              >
                {{ __('Clear All') }}
              </button>
            </div>

            <!-- Two-Column Side-by-Side Body -->
            <div class="flex flex-row min-h-[280px] max-h-[380px] !bg-white dark:!bg-[#1e293b]">
              <!-- Left Pane: 6 Categories -->
              <div class="w-44 shrink-0 border-r border-outline-gray-2 dark:border-outline-gray-7 py-1.5 overflow-y-auto !bg-[#f8fafc] dark:!bg-[#0f172a]">
                <button
                  v-for="cat in filterCategories"
                  :key="cat.key"
                  type="button"
                  class="w-full group flex items-center justify-between px-3 py-2 text-xs text-left transition-colors cursor-pointer"
                  :class="activeFilterCategory === cat.key ? '!bg-white dark:!bg-[#1e293b] font-bold text-ink-gray-9 dark:text-ink-white shadow-xs' : 'text-ink-gray-7 hover:!bg-slate-200/70 dark:text-ink-gray-3 dark:hover:!bg-slate-800'"
                  @click="activeFilterCategory = cat.key"
                  @mouseenter="activeFilterCategory = cat.key"
                >
                  <div class="flex items-center gap-2 truncate">
                    <component :is="cat.icon" class="size-3.5 text-ink-gray-5 shrink-0" />
                    <span class="truncate">{{ __(cat.label) }}</span>
                  </div>
                  <div class="flex items-center gap-1 shrink-0">
                    <span
                      v-if="activeFilters[cat.key]?.size > 0"
                      class="size-1.5 rounded-full bg-primary-500"
                    />
                    <LucideChevronRight class="size-3 text-ink-gray-4 group-hover:text-ink-gray-7" />
                  </div>
                </button>
              </div>

              <!-- Right Pane: Filter Options for Active Category -->
              <div class="flex-1 min-w-0 p-3 flex flex-col overflow-hidden !bg-white dark:!bg-[#1e293b]">
                <!-- Active Category Header -->
                <div class="flex items-center justify-between pb-2 mb-2 border-b border-outline-gray-2 dark:border-outline-gray-7">
                  <span class="text-xs font-bold uppercase tracking-wider text-ink-gray-6 dark:text-ink-gray-3">
                    {{ getActiveCategoryLabel() }}
                  </span>
                  <span class="text-[11px] text-ink-gray-4">
                    {{ getActiveCategoryOptions().length }} {{ __('options') }}
                  </span>
                </div>

                <!-- Scrollable Options List -->
                <div class="flex-1 overflow-y-auto space-y-1 pr-1 max-h-[290px] min-h-[190px]">
                  <div
                    v-if="getActiveCategoryOptions().length === 0"
                    class="py-8 text-center text-xs text-ink-gray-4 italic"
                  >
                    {{ __('No filter values available for this category.') }}
                  </div>

                  <label
                    v-for="opt in getActiveCategoryOptions()"
                    :key="opt.value"
                    class="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-xs transition-colors hover:!bg-slate-100 dark:hover:!bg-slate-700/60 select-none !bg-white dark:!bg-[#1e293b]"
                  >
                    <div class="flex items-center gap-2 min-w-0 flex-1">
                      <input
                        type="checkbox"
                        :checked="activeFilters[activeFilterCategory]?.has(opt.value)"
                        class="size-3.5 rounded border-outline-gray-3 text-ink-primary focus:ring-0 shrink-0 cursor-pointer"
                        @change="toggleFilterValue(activeFilterCategory, opt.value)"
                      />
                      <span class="truncate text-ink-gray-8 dark:text-ink-gray-2" :title="opt.label">
                        {{ opt.label }}
                      </span>
                    </div>
                    <span v-if="opt.count !== undefined" class="text-[10px] text-ink-gray-4 font-mono shrink-0">
                      {{ opt.count }}
                    </span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Dropdown Footer -->
            <div class="flex items-center justify-between px-3.5 py-2 border-t border-outline-gray-2 dark:border-outline-gray-7 !bg-[#f8fafc] dark:!bg-[#0f172a] text-xs">
              <span class="text-ink-gray-5 text-[11px]">
                {{ totalActiveFiltersCount > 0 ? __('{0} filters selected', [totalActiveFiltersCount]) : __('No filters applied') }}
              </span>
              <button
                type="button"
                class="rounded-md bg-surface-gray-9 px-3 py-1 font-semibold text-surface-white hover:bg-black dark:bg-surface-white dark:text-ink-gray-9 text-xs cursor-pointer"
                @click="showFilterMenu = false"
              >
                {{ __('Done') }}
              </button>
            </div>
          </div>
        </div>

        <!-- 3. Export Button -->
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs font-semibold text-ink-gray-8 shadow-2xs transition-colors hover:bg-surface-gray-2 dark:border-outline-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-2"
          @click="exportTasksToCSV"
        >
          <LucideDownload class="size-3.5 text-ink-gray-5" />
          <span>{{ __('Export') }}</span>
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="flex-1 space-y-4 p-4 sm:p-5">
      <!-- Status Tabs Bar (Compact horizontal layout matching reference) -->
      <div class="rounded-xl border border-outline-gray-2 bg-surface-base px-3 py-2 shadow-xs dark:border-outline-gray-7">
        <div class="flex items-center gap-2 overflow-x-auto">
          <button
            v-for="st in statusPills"
            :key="st.value"
            type="button"
            class="flex items-center gap-2 rounded-md px-3.5 py-1.5 text-xs transition-all whitespace-nowrap focus:outline-none"
            :class="[
              currentStatus === st.value
                ? 'bg-[#18202f] text-white font-semibold shadow-xs dark:bg-surface-white dark:text-ink-gray-9'
                : 'text-ink-gray-7 hover:bg-surface-gray-2 hover:text-ink-gray-9 dark:text-ink-gray-3 dark:hover:bg-surface-gray-8 dark:hover:text-ink-white',
            ]"
            @click="currentStatus = st.value"
          >
            <span>{{ st.label }}</span>
            <span
              class="rounded-full px-2 py-0.5 text-[11px] font-bold leading-none"
              :class="[
                currentStatus === st.value
                  ? 'bg-white/20 text-white dark:bg-surface-gray-8 dark:text-ink-gray-9'
                  : 'bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3',
              ]"
            >
              {{ getCountForStatus(st.value) }}
            </span>
          </button>
        </div>
      </div>

      <!-- Tasks Section -->
      <div class="rounded border border-outline-gray-2 bg-surface-base shadow-sm dark:border-outline-gray-7">
        <!-- Search & Info Toolbar with Bulk Actions -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-4 py-2.5 dark:border-outline-gray-7">
          <div class="flex items-center gap-2">
            <h2 class="text-xs font-semibold text-ink-gray-9 dark:text-ink-white">
              {{ __('Tasks List') }}
            </h2>
            <Badge variant="outline" size="sm">
              {{ totalTasksCount }} {{ __('tasks') }}
            </Badge>

            <!-- Selected items indicator & Three-Dot Bulk Actions -->
            <template v-if="selectedCount">
              <Badge
                variant="solid"
                size="sm"
                class="bg-surface-gray-9 text-surface-white dark:bg-surface-white dark:text-ink-gray-9"
              >
                {{ selectedCount }} {{ __('selected') }}
              </Badge>

              <!-- Three-Dot Bulk Actions Dropdown -->
              <Dropdown :options="bulkActionOptions">
                <Button
                  icon="lucide-more-horizontal"
                  variant="ghost"
                  class="!size-7 p-1 text-ink-gray-7 hover:text-ink-gray-9 dark:text-ink-gray-3"
                />
              </Dropdown>
            </template>
          </div>

          <div class="w-full sm:w-72">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="__('Search prospect, company, email, country, timezone...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>

        <!-- Task Table: Dense, compact 10-column prospect table with uniform, responsive layout -->
        <div class="overflow-x-auto">
          <table class="w-full table-fixed text-left text-xs">
            <thead class="bg-surface-gray-1 text-ink-gray-5 border-b border-outline-gray-2 dark:bg-surface-gray-8 dark:border-outline-gray-7">
              <tr>
                <th class="w-[3%] px-1.5 py-1.5 text-center shrink-0">
                  <input
                    ref="headerCheckboxRef"
                    type="checkbox"
                    :checked="isAllSelected"
                    :disabled="!filteredTasks.length"
                    class="size-3.5 cursor-pointer rounded border-outline-gray-3 text-ink-primary focus:ring-0 disabled:opacity-40"
                    @change="toggleSelectAll"
                  />
                </th>
                <th class="w-[15%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Name') }}</th>
                <th class="w-[9%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Designation') }}</th>
                <th class="w-[13%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Email') }}</th>
                <th class="w-[9%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Phone') }}</th>
                <th class="w-[6%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Country') }}</th>
                <th class="w-[8%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Timezone') }}</th>
                <th class="w-[5%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Data Age') }}</th>
                <th class="w-[7%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Last Updated') }}</th>
                <th class="w-[8%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Assigned By') }}</th>
                <th class="w-[8%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px]">{{ __('Assigned To') }}</th>
                <th class="w-[8%] px-2 py-1.5 font-semibold uppercase tracking-wider text-[10px] text-right shrink-0">{{ __('Actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-2 dark:divide-outline-gray-7">
              <tr
                v-for="task in filteredTasks"
                :key="task.name"
                class="cursor-pointer transition-colors hover:bg-surface-gray-2/70 dark:hover:bg-surface-gray-8/70"
                :class="{ 'bg-surface-gray-1/40 dark:bg-surface-gray-8/30': selectedTaskSet.has(task.name) }"
                @click="handleRowClick(task)"
              >
                <!-- Row Checkbox -->
                <td class="w-[3%] px-1.5 py-1.5 text-center shrink-0" @click.stop>
                  <input
                    type="checkbox"
                    :checked="selectedTaskSet.has(task.name)"
                    @change="toggleTaskSelection(task.name, $event.target.checked)"
                    class="size-3.5 cursor-pointer rounded border-outline-gray-3 text-ink-primary focus:ring-0"
                    @click.stop
                  />
                </td>

                <!-- 1. Name & Organization underneath -->
                <td class="w-[15%] px-2 py-1.5">
                  <div class="flex flex-col min-w-0">
                    <router-link
                      :to="{
                        name: 'TaskProspect',
                        params: { contactId: task.contact },
                        query: { taskId: task.name },
                      }"
                      class="truncate text-[11.5px] font-semibold leading-tight text-ink-gray-9 hover:underline hover:text-ink-primary dark:text-ink-white"
                      :title="task.contact_name || task.prospect_name || ''"
                      @click.stop
                    >
                      {{ task.contact_name || task.prospect_name || '—' }}
                    </router-link>
                    <span
                      v-if="task.organization"
                      class="truncate text-[10px] leading-tight text-ink-gray-5 dark:text-ink-gray-4"
                      :title="task.organization"
                    >
                      {{ task.organization }}
                    </span>
                  </div>
                </td>

                <!-- 2. Designation -->
                <td class="w-[9%] px-2 py-1.5 text-ink-gray-8 dark:text-ink-gray-2">
                  <div class="truncate text-[11px] leading-tight" :title="task.designation || ''">
                    {{ task.designation || '—' }}
                  </div>
                </td>

                <!-- 3. Email -->
                <td class="w-[13%] px-2 py-1.5 text-ink-gray-7 dark:text-ink-gray-3">
                  <div class="truncate text-[11px] leading-tight" :title="task.email || ''">
                    {{ task.email || '—' }}
                  </div>
                </td>

                <!-- 4. Phone -->
                <td class="w-[9%] px-2 py-1.5 text-ink-gray-7 dark:text-ink-gray-3 whitespace-nowrap">
                  <div class="truncate text-[11px] leading-tight" :title="task.mobile_no || ''">
                    {{ task.mobile_no || '—' }}
                  </div>
                </td>

                <!-- 5. Country -->
                <td class="w-[6%] px-2 py-1.5 text-ink-gray-8 dark:text-ink-gray-2">
                  <div class="truncate text-[11px] leading-tight" :title="task._displayCountry || ''">
                    {{ task._displayCountry || '—' }}
                  </div>
                </td>

                <!-- 6. Timezone -->
                <td class="w-[8%] px-2 py-1.5 font-mono text-[10.5px] leading-tight text-ink-gray-7 dark:text-ink-gray-3 whitespace-nowrap">
                  <div class="truncate" :title="task._displayTimezone || ''">
                    {{ task._displayTimezone || '—' }}
                  </div>
                </td>

                <!-- 7. Data Age -->
                <td class="w-[5%] px-2 py-1.5 text-[11px] leading-tight text-ink-gray-7 dark:text-ink-gray-3 whitespace-nowrap">
                  <div class="truncate" :title="task._formattedCreation || ''">
                    {{ task._dataAge || '—' }}
                  </div>
                </td>

                <!-- 8. Last Updated -->
                <td class="w-[7%] px-2 py-1.5 text-[11px] leading-tight text-ink-gray-7 dark:text-ink-gray-3 whitespace-nowrap">
                  <div class="truncate" :title="task._formattedModified || ''">
                    {{ task._timeAgo || '—' }}
                  </div>
                </td>

                <!-- 9. Assigned By -->
                <td class="w-[8%] px-2 py-1.5 text-ink-gray-8 dark:text-ink-gray-2">
                  <div class="truncate text-[11px] leading-tight" :title="task.allocated_by_name || task.allocated_by || ''">
                    {{ task.allocated_by_name || task.allocated_by || '—' }}
                  </div>
                </td>

                <!-- 10. Assigned To -->
                <td class="w-[8%] px-2 py-1.5 text-ink-gray-8 dark:text-ink-gray-2">
                  <div class="truncate text-[11px] leading-tight" :title="task.assigned_to_name || task.assigned_to || ''">
                    {{ task.assigned_to_name || task.assigned_to || '—' }}
                  </div>
                </td>

                <!-- 10. Actions Column: 1. Email, 2. Phone, 3. Pencil/Edit -->
                <td class="w-[8%] px-2 py-1.5 text-right whitespace-nowrap shrink-0" @click.stop>
                  <div class="inline-flex items-center gap-1 justify-end" @click.stop>
                    <!-- 1. Email icon -->
                    <Button
                      variant="subtle"
                      icon="lucide-mail"
                      :tooltip="__('Send Email')"
                      class="!size-6 p-0.5 text-ink-blue-3 hover:bg-surface-blue-2"
                      @click.stop="openTaskEmail(task)"
                    />
                    <!-- 2. Phone icon -->
                    <Button
                      variant="subtle"
                      icon="lucide-phone"
                      :tooltip="task.mobile_no ? __('Make Call') : __('No phone number available')"
                      class="!size-6 p-0.5 text-ink-green-3 hover:bg-surface-green-2"
                      :class="{ 'opacity-40': !task.mobile_no }"
                      @click.stop="handlePhoneAction(task)"
                    />
                    <!-- 3. Pencil/Edit icon -->
                    <Dropdown :options="getStatusDropdownOptions(task)" @click.stop>
                      <Button
                        variant="subtle"
                        icon="lucide-edit-2"
                        :tooltip="__('Update Status')"
                        class="!size-6 p-0.5 text-ink-gray-7 hover:text-ink-gray-9 hover:bg-surface-gray-2 dark:text-ink-gray-3"
                        @click.stop
                      />
                    </Dropdown>
                  </div>
                </td>
              </tr>

              <!-- Empty Row -->
              <tr v-if="!filteredTasks.length">
                <td :colspan="12" class="px-5 py-12 text-center text-ink-gray-5">
                  <div class="flex flex-col items-center justify-center gap-2">
                    <TaskIcon class="size-8 text-ink-gray-4" />
                    <p class="font-medium">{{ __('No tasks match your filter criteria.') }}</p>
                    <p class="text-xs text-ink-gray-4">{{ __('Assigned tasks from Daily Allocation appear here automatically.') }}</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination Footer matching Contacts page -->
        <ListFooter
          v-if="totalTasksCount > 0"
          v-model="pageSize"
          class="border-t border-outline-gray-2 px-3 py-2 sm:px-5 dark:border-outline-gray-7"
          :options="{
            rowCount: tasks.length,
            totalCount: totalTasksCount,
            pageLengthOptions: [20, 50, 100],
          }"
          @loadMore="handleLoadMore"
        >
          <template #right>
            <div class="flex items-center">
              <Button
                v-if="tasks.length < totalTasksCount"
                :label="__('Load More')"
                :loading="loadingMore"
                :disabled="loadingMore"
                @click="handleLoadMore"
              />
              <div
                v-if="tasks.length < totalTasksCount"
                class="mx-3 h-4 border-l border-outline-gray-2 dark:border-outline-gray-7"
              />
              <div class="flex items-center gap-1 text-sm text-ink-gray-5">
                <div>{{ tasks.length }}</div>
                <div>{{ __('of') }}</div>
                <div>{{ totalTasksCount }}</div>
              </div>
            </div>
          </template>
        </ListFooter>
      </div>
    </div>

    <!-- UPDATE SINGLE TASK MODAL -->
    <Dialog
      v-model="showEditModal"
      :options="{
        title: __('Update Task Progress'),
        size: 'lg',
      }"
    >
      <template #body-content>
        <div v-if="selectedTask" class="space-y-4 text-xs">
          <!-- Prospect Details Summary -->
          <div class="rounded bg-surface-gray-2 p-3 dark:bg-surface-gray-8">
            <div class="font-semibold text-ink-gray-9 dark:text-ink-white">{{ selectedTask.contact_name }}</div>
            <div class="text-ink-gray-5">
              {{ selectedTask.organization ? selectedTask.organization + ' • ' : '' }}
              {{ selectedTask.email }} • {{ selectedTask.mobile_no }}
            </div>
            <div class="mt-1 text-[11px] text-ink-gray-4">
              {{ __('Allocated for:') }} {{ selectedTask.allocation_date }} | {{ __('Assigned to:') }} {{ selectedTask.assigned_to_name }}
            </div>
          </div>

          <!-- Status Dropdown -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Status *') }}
            </label>
            <select
              v-model="editForm.status"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="To Do">{{ __('To Do') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Pending">{{ __('Pending') }}</option>
              <option value="Callback">{{ __('Callback') }}</option>
              <option value="Follow up">{{ __('Follow up') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
            </select>
          </div>

          <!-- Follow-up Date -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Follow-up Date (optional)') }}
            </label>
            <input
              v-model="editForm.follow_up_date"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <!-- Notes Textarea -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Notes & Remarks') }}
            </label>
            <textarea
              v-model="editForm.notes"
              rows="4"
              :placeholder="__('Record notes from your discussion, call outcome, next steps...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="showEditModal = false"
        />
        <Button
          variant="solid"
          :loading="saving"
          :label="__('Save Progress')"
          @click="submitEdit"
        />
      </template>
    </Dialog>

    <!-- BULK EDIT MODAL -->
    <Dialog
      v-model:open="showBulkEditModal"
      :title="__('Bulk Edit Tasks')"
      size="md"
    >
      <template #default>
        <div class="space-y-4 text-xs">
          <p class="text-ink-gray-5">
            {{ __('Update workflow status, follow-up date, or remarks for {0} selected task(s).', [selectedTaskIds.length]) }}
          </p>

          <!-- Status Dropdown -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Task Workflow Status') }}
            </label>
            <select
              v-model="bulkEditForm.status"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="">{{ __('Keep current status') }}</option>
              <option value="To Do">{{ __('To Do') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Pending">{{ __('Pending') }}</option>
              <option value="Callback">{{ __('Callback') }}</option>
              <option value="Follow up">{{ __('Follow up') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
            </select>
          </div>

          <!-- Follow-up Date -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Follow-up Date') }}
            </label>
            <input
              v-model="bulkEditForm.follow_up_date"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <!-- Notes -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Notes & Remarks') }}
            </label>
            <textarea
              v-model="bulkEditForm.notes"
              rows="3"
              :placeholder="__('Add notes to selected tasks...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showBulkEditModal = false"
          />
          <Button
            variant="solid"
            :loading="bulkSaving"
            :label="__('Update {0} Tasks', [selectedTaskIds.length])"
            @click="submitBulkEdit"
          />
        </div>
      </template>
    </Dialog>

    <!-- ADMIN BULK ASSIGN MODAL -->
    <Dialog
      v-model:open="showAssignModal"
      :title="__('Assign Tasks')"
      size="md"
    >
      <template #default>
        <div class="space-y-4 text-xs">
          <p class="text-ink-gray-5">
            {{ __('Reassign {0} selected task(s) to a team member.', [selectedTaskIds.length]) }}
          </p>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Assign To *') }}
            </label>
            <select
              v-model="bulkAssignTargetUser"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="">{{ __('Select a user...') }}</option>
              <option
                v-for="u in assignableUsers"
                :key="u.name"
                :value="u.name"
              >
                {{ u.full_name }} ({{ u.email }})
              </option>
            </select>
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showAssignModal = false"
          />
          <Button
            variant="solid"
            :loading="bulkAssigning"
            :disabled="!bulkAssignTargetUser"
            :label="__('Assign Tasks')"
            @click="submitBulkAssign"
          />
        </div>
      </template>
    </Dialog>

    <!-- BULK EMAIL MODAL -->
    <BulkEmailModal
      v-if="showBulkEmailModal"
      v-model="showBulkEmailModal"
      doctype="CRM Daily Allocation"
      :selectedValues="selectedTaskIds"
      @reload="onBulkEmailReload"
    />

    <!-- TASK EMAIL MODAL WITH UNIFIED VISUAL EDITOR -->
    <Dialog
      v-model:open="showTaskEmailModal"
      :title="__('Send Email to {0}', [activeEmailTask?.contact_name || 'Prospect'])"
      size="xl"
    >
      <template #default>
        <div class="space-y-3 py-2 text-xs">
          <!-- Recipient & CC/BCC inputs -->
          <div class="space-y-2">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Recipient Email *') }}</label>
              <input
                v-model="taskEmailForm.recipient"
                type="email"
                placeholder="recipient@example.com"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('CC (optional)') }}</label>
                <input
                  v-model="taskEmailForm.cc"
                  type="text"
                  placeholder="cc@example.com"
                  class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
                />
              </div>
              <div>
                <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('BCC (optional)') }}</label>
                <input
                  v-model="taskEmailForm.bcc"
                  type="text"
                  placeholder="bcc@example.com"
                  class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
                />
              </div>
            </div>
          </div>

          <!-- Unified Visual Email Editor -->
          <VisualEmailEditor
            ref="taskVisualEditorRef"
            v-model:subject="taskEmailForm.subject"
            v-model:content="taskEmailForm.content"
            v-model:templateName="taskEmailForm.templateName"
            v-model:isBranded="taskEmailForm.isBranded"
            :recipientCount="1"
            :sampleRecipient="{
              full_name: activeEmailTask?.contact_name || 'Prospect',
              first_name: activeEmailTask?.contact_name?.split(' ')[0] || 'there',
              organization: activeEmailTask?.company || 'Organization',
              email: taskEmailForm.recipient,
            }"
            :contactName="activeEmailTask?.contact || null"
            defaultMode="edit"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center justify-between w-full">
          <div>
            <Button
              v-if="taskVisualEditorRef?.activeMode === 'edit'"
              variant="outline"
              size="sm"
              iconLeft="lucide-eye"
              :label="__('Preview')"
              @click="taskVisualEditorRef?.switchToPreview()"
            />
            <Button
              v-else
              variant="outline"
              size="sm"
              iconLeft="lucide-pen"
              :label="__('Edit')"
              @click="taskVisualEditorRef && (taskVisualEditorRef.activeMode = 'edit')"
            />
          </div>
          <div class="flex items-center gap-2">
            <Button
              variant="subtle"
              :label="__('Cancel')"
              @click="showTaskEmailModal = false"
            />
            <Button
              variant="solid"
              :loading="taskEmailSending"
              :disabled="!taskEmailForm.recipient || !taskEmailForm.subject || !taskEmailForm.content"
              :label="__('Send Email')"
              @click="submitTaskEmail"
            />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- TASK CALL MODAL -->
    <Dialog
      v-model:open="showTaskCallModal"
      :title="__('Log Call with {0}', [activeCallTask?.contact_name || 'Prospect'])"
      size="md"
    >
      <template #default>
        <div class="space-y-3 py-2 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Call Type') }}</label>
              <select
                v-model="taskCallForm.type"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              >
                <option value="Outgoing">{{ __('Outgoing') }}</option>
                <option value="Incoming">{{ __('Incoming') }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Status') }}</label>
              <select
                v-model="taskCallForm.status"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              >
                <option value="Completed">{{ __('Completed') }}</option>
                <option value="No Answer">{{ __('No Answer') }}</option>
                <option value="Busy">{{ __('Busy') }}</option>
                <option value="Failed">{{ __('Failed') }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Phone Number *') }}</label>
              <input
                v-model="taskCallForm.phone"
                type="text"
                placeholder="+1 234 567 8900"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Duration (seconds or mm:ss)') }}</label>
              <input
                v-model="taskCallForm.duration"
                type="text"
                placeholder="150 or 02:30"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Notes & Remarks') }}</label>
            <textarea
              v-model="taskCallForm.note"
              rows="3"
              placeholder="Record call discussion, questions asked, next steps..."
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showTaskCallModal = false"
          />
          <Button
            variant="solid"
            :loading="taskCallSaving"
            :disabled="!taskCallForm.phone"
            :label="__('Log Call')"
            @click="submitTaskCall"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, shallowRef, reactive, computed, watch, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { call, Button, Dialog, Badge, Dropdown, Tooltip, toast } from 'frappe-ui'
import { ListFooter } from 'frappe-ui/experimental'
import { globalStore } from '@/stores/global'
import { formatDate, timeAgo } from '@/utils'
import { callEnabled } from '@/composables/telephony'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import BulkEmailModal from '@/components/Modals/BulkEmailModal.vue'
import VisualEmailEditor from '@/components/VisualEmailEditor.vue'
import LucideUsers from '~icons/lucide/users'
import LucideUser from '~icons/lucide/user'
import LucideFilter from '~icons/lucide/filter'
import LucideDownload from '~icons/lucide/download'
import LucideBriefcase from '~icons/lucide/briefcase'
import LucideGlobe from '~icons/lucide/globe'
import LucideClock from '~icons/lucide/clock'
import LucideCalendar from '~icons/lucide/calendar'
import LucideDatabase from '~icons/lucide/database'
import LucideChevronRight from '~icons/lucide/chevron-right'

const router = useRouter()
const { $dialog, $socket, makeCall } = globalStore()

function openStandaloneDialpad() {
  makeCall('')
}

function handleRowClick(task) {
  // If user is highlighting text to copy, do not navigate
  const selection = window.getSelection ? window.getSelection().toString() : ''
  if (selection && selection.trim().length > 0) return

  if (!task?.contact) return
  try {
    sessionStorage.setItem('active_task_' + task.name, JSON.stringify(task))
  } catch (e) {}
  router.push({
    name: 'TaskProspect',
    params: { contactId: task.contact },
    query: { taskId: task.name },
  })
}

const todayStr = new Date().toLocaleDateString('en-CA')
const loading = ref(false)
const loadingMore = ref(false)
const isAdmin = ref(false)
const selectedUser = ref('all')
const dateFilterMode = ref('all')
const customDate = ref(todayStr)
const currentStatus = ref('To Do')
const searchQuery = ref('')
const pageSize = ref(20)
const totalTasksCount = ref(0)
const serverStatusCounts = ref({})
let isAdminLoaded = false

const tasks = ref([])
const assignableUsers = ref([])
const selectedTaskSet = shallowRef(new Set())
const selectedTaskIds = computed({
  get: () => Array.from(selectedTaskSet.value),
  set: (newIds) => {
    selectedTaskSet.value = new Set(newIds || [])
  },
})
const selectedCount = computed(() => selectedTaskSet.value.size)

function toggleTaskSelection(name, checked) {
  const newSet = new Set(selectedTaskSet.value)
  if (checked) {
    newSet.add(name)
  } else {
    newSet.delete(name)
  }
  selectedTaskSet.value = newSet
}
const headerCheckboxRef = ref(null)

// Flyout Filter & Top Header Dropdowns State
const showFilterMenu = ref(false)
const activeFilterCategory = ref('designation')
const filterDropdownContainerRef = ref(null)

const activeFilters = reactive({
  designation: new Set(),
  country: new Set(),
  timezone: new Set(),
  assigned_by: new Set(),
  last_updated: new Set(),
  data_age: new Set(),
})

const filterCategories = [
  { key: 'designation', label: 'Designation', icon: LucideBriefcase },
  { key: 'country', label: 'Country', icon: LucideGlobe },
  { key: 'timezone', label: 'Timezone', icon: LucideClock },
  { key: 'assigned_by', label: 'Assigned by', icon: LucideUser },
  { key: 'last_updated', label: 'Last updated', icon: LucideCalendar },
  { key: 'data_age', label: 'Data age', icon: LucideDatabase },
]

function getActiveCategoryLabel() {
  const cat = filterCategories.find((c) => c.key === activeFilterCategory.value)
  return cat ? cat.label : ''
}

function getDateBucket(dateStr) {
  if (!dateStr) return 'Older'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return 'Older'
  const diffDays = Math.floor((new Date() - d) / (1000 * 60 * 60 * 24))
  if (diffDays <= 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays <= 3) return '2-3 days ago'
  if (diffDays <= 7) return '4-7 days ago'
  return 'Over 7 days ago'
}

function getActiveCategoryOptions() {
  const all = tasks.value || []
  const counts = {}

  if (activeFilterCategory.value === 'designation') {
    all.forEach((t) => {
      const val = (t.designation || '').trim()
      if (val) counts[val] = (counts[val] || 0) + 1
    })
  } else if (activeFilterCategory.value === 'country') {
    all.forEach((t) => {
      const val = (t.country || '').trim()
      if (val) counts[val] = (counts[val] || 0) + 1
    })
  } else if (activeFilterCategory.value === 'timezone') {
    all.forEach((t) => {
      const val = (t.timezone || '').trim()
      if (val) counts[val] = (counts[val] || 0) + 1
    })
  } else if (activeFilterCategory.value === 'assigned_by') {
    all.forEach((t) => {
      const val = (t.assigned_by || t.allocated_by || '').trim()
      if (val) counts[val] = (counts[val] || 0) + 1
    })
  } else if (activeFilterCategory.value === 'last_updated') {
    all.forEach((t) => {
      const bucket = getDateBucket(t.modified)
      counts[bucket] = (counts[bucket] || 0) + 1
    })
  } else if (activeFilterCategory.value === 'data_age') {
    all.forEach((t) => {
      const bucket = getDateBucket(t.data_age_date || t.modified)
      counts[bucket] = (counts[bucket] || 0) + 1
    })
  }

  return Object.keys(counts)
    .sort()
    .map((k) => ({
      label: k,
      value: k,
      count: counts[k],
    }))
}

function toggleFilterValue(category, val) {
  const set = activeFilters[category]
  if (!set) return
  if (set.has(val)) {
    set.delete(val)
  } else {
    set.add(val)
  }
}

function clearAllFilters() {
  activeFilters.designation.clear()
  activeFilters.country.clear()
  activeFilters.timezone.clear()
  activeFilters.assigned_by.clear()
  activeFilters.last_updated.clear()
  activeFilters.data_age.clear()
}

const totalActiveFiltersCount = computed(() => {
  return (
    activeFilters.designation.size +
    activeFilters.country.size +
    activeFilters.timezone.size +
    activeFilters.assigned_by.size +
    activeFilters.last_updated.size +
    activeFilters.data_age.size
  )
})

const currentUserName = computed(() => {
  return window.frappe?.session?.user_fullname || window.frappe?.session?.user || 'My Tasks'
})

const selectedUserLabel = computed(() => {
  if (selectedUser.value === 'all') return 'All Users'
  const u = assignableUsers.value.find((usr) => usr.name === selectedUser.value)
  return u ? (u.full_name || u.email) : selectedUser.value
})

const userDropdownOptions = computed(() => {
  const opts = [
    {
      label: 'All Users',
      onClick: () => {
        selectedUser.value = 'all'
        fetchTasks()
      },
    },
  ]
  assignableUsers.value.forEach((u) => {
    opts.push({
      label: `${u.full_name || u.name} (${u.email || u.name})`,
      onClick: () => {
        selectedUser.value = u.name
        fetchTasks()
      },
    })
  })
  return opts
})

function exportTasksToCSV() {
  const visible = filteredTasks.value || []
  if (!visible.length) {
    toast.error(__('No tasks to export.'))
    return
  }

  const headers = [
    'Name',
    'Designation',
    'Organization',
    'Email',
    'Phone',
    'Country',
    'Timezone',
    'Data Age',
    'Last Updated',
    'Assigned By',
    'Status',
  ]

  const rows = visible.map((t) => [
    t.contact_name || t.name || '',
    t.designation || '',
    t.organization || '',
    t.email || '',
    t.mobile_no || t.phone || '',
    t.country || '',
    t.timezone || '',
    t.data_age_text || timeAgo(t.modified) || '',
    formatDate(t.modified) || '',
    t.assigned_by || t.allocated_by || '',
    t.status || '',
  ])

  const csvContent = [
    headers.map((h) => `"${String(h).replace(/"/g, '""')}"`).join(','),
    ...rows.map((r) =>
      r.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(','),
    ),
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute(
    'download',
    `my-tasks-${currentStatus.value.toLowerCase().replace(/\s+/g, '-')}-${todayStr}.csv`,
  )
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  toast.success(__('Exported {0} tasks successfully.', [visible.length]))
}

// Single Edit Modal
const showEditModal = ref(false)
const saving = ref(false)
const selectedTask = ref(null)
const editForm = reactive({
  status: 'To Do',
  follow_up_date: '',
  notes: '',
})

// Bulk Modals
const showBulkEditModal = ref(false)
const bulkSaving = ref(false)
const bulkEditForm = reactive({
  status: '',
  follow_up_date: '',
  notes: '',
})

const showAssignModal = ref(false)
const bulkAssigning = ref(false)
const bulkAssignTargetUser = ref('')

const showBulkEmailModal = ref(false)

// Task Email & Call Modals
const showTaskEmailModal = ref(false)
const activeEmailTask = ref(null)
const taskEmailSending = ref(false)
const taskVisualEditorRef = ref(null)
const taskEmailForm = reactive({
  recipient: '',
  subject: '',
  cc: '',
  bcc: '',
  content: '',
  templateName: '',
  isBranded: false,
})

const showTaskCallModal = ref(false)
const activeCallTask = ref(null)
const taskCallSaving = ref(false)
const taskCallForm = reactive({
  type: 'Outgoing',
  status: 'Completed',
  phone: '',
  duration: '02:30',
  note: '',
})

const statusPills = [
  { label: 'To Do', value: 'To Do', badgeClass: 'bg-surface-gray-2 text-ink-gray-7' },
  { label: 'In Progress', value: 'In Progress', badgeClass: 'bg-surface-blue-2 text-ink-blue-3' },
  { label: 'Pending', value: 'Pending', badgeClass: 'bg-surface-amber-2 text-ink-amber-3' },
  { label: 'Callback', value: 'Callback', badgeClass: 'bg-surface-purple-2 text-ink-purple-3' },
  { label: 'Follow up', value: 'Follow up', badgeClass: 'bg-surface-teal-2 text-ink-teal-3' },
  { label: 'Not Interested', value: 'Not Interested', badgeClass: 'bg-surface-gray-3 text-ink-gray-7' },
]

const myTaskStatuses = [
  'To Do',
  'In Progress',
  'Pending',
  'Callback',
  'Follow up',
  'Not Interested',
]

const TZ_FALLBACK_MAP = {
  'Asia/Kolkata': 'GMT+5:30 (IST)',
  'Asia/Singapore': 'GMT+8 (SGT)',
  'Asia/Kuala_Lumpur': 'GMT+8 (MYT)',
  'Europe/London': 'GMT+0 (GMT)',
  'America/New_York': 'GMT-5 (EST)',
  'America/Chicago': 'GMT-6 (CST)',
  'America/Los_Angeles': 'GMT-8 (PST)',
  'Australia/Sydney': 'GMT+11 (AEDT)',
  'Asia/Dubai': 'GMT+4 (GST)',
  'Asia/Tokyo': 'GMT+9 (JST)',
}

function formatTimezone(tz) {
  if (!tz || tz === 'Not Available' || tz === '—') return '—'
  if (String(tz).startsWith('GMT')) return tz
  return TZ_FALLBACK_MAP[tz] || tz
}

function formatDataAge(dateStr) {
  if (!dateStr) return '—'
  return timeAgo(dateStr) || '—'
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '—'
  return timeAgo(dateStr) || '—'
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  return formatDate(dateStr, 'DD MMM YYYY, hh:mm A')
}

function handlePhoneAction(task) {
  if (!task.mobile_no) {
    toast.error(__('No phone number available for this prospect'))
    return
  }
  makeCall(task.mobile_no)
}

const taskDropdownCache = new WeakMap()

function getStatusDropdownOptions(task) {
  if (!task) return []
  const cached = taskDropdownCache.get(task)
  if (cached && cached.status === task.status) {
    return cached.options
  }

  const options = myTaskStatuses.map((st) => ({
    label: st + (task.status === st ? ' ✓' : ''),
    onClick: () => handleStatusChange(task, st),
  }))

  options.push({
    label: __('Edit notes & follow-up...'),
    icon: 'lucide-file-text',
    onClick: () => openEditModal(task),
  })

  options.push({
    label: __('Log Call...'),
    icon: 'lucide-phone-call',
    onClick: () => openTaskCall(task),
  })

  taskDropdownCache.set(task, { status: task.status, options })
  return options
}

// Three-Dot Bulk Actions
const bulkActionOptions = computed(() => {
  const actions = []

  // 1. Edit
  actions.push({
    label: __('Edit'),
    onClick: () => openBulkEditModal(),
  })

  // 2. Delete (Admin only)
  if (isAdmin.value) {
    actions.push({
      label: __('Delete'),
      onClick: () => confirmBulkDelete(),
    })
  }

  // 3. Assign To (Admin only)
  if (isAdmin.value) {
    actions.push({
      label: __('Assign To'),
      onClick: () => {
        bulkAssignTargetUser.value = ''
        showAssignModal.value = true
      },
    })

    // 4. Clear Assignment (Admin only)
    actions.push({
      label: __('Clear Assignment'),
      onClick: () => confirmClearAssignment(),
    })
  }

  // 5. Convert to Deal
  actions.push({
    label: __('Convert to Deal'),
    onClick: () => confirmConvertToDeal(),
  })

  // 6. Bulk Email
  actions.push({
    label: __('Bulk Email'),
    onClick: () => {
      showBulkEmailModal.value = true
    },
  })

  // 7. Change Status (with submenu containing the 6 My Task Statuses)
  actions.push({
    label: __('Change Status'),
    submenu: myTaskStatuses.map((st) => ({
      label: __(st),
      onClick: () => applyTaskStatus(st),
    })),
  })

  return actions
})

function openBulkEditModal() {
  bulkEditForm.status = ''
  bulkEditForm.follow_up_date = ''
  bulkEditForm.notes = ''
  showBulkEditModal.value = true
}

async function submitBulkEdit() {
  bulkSaving.value = true
  try {
    const res = await call('crm.api.daily_allocation.bulk_update_tasks', {
      tasks: selectedTaskIds.value,
      status: bulkEditForm.status || null,
      notes: bulkEditForm.notes ? bulkEditForm.notes : null,
      follow_up_date: bulkEditForm.follow_up_date || null,
    })
    toast.success(res.message || __('Tasks updated successfully.'))
    showBulkEditModal.value = false
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update tasks.'))
  } finally {
    bulkSaving.value = false
  }
}

function confirmBulkDelete() {
  $dialog({
    title: __('Delete Tasks'),
    message: __('Are you sure you want to delete {0} selected task(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_delete_tasks', {
              tasks: selectedTaskIds.value,
            })
            toast.success(res.message || __('Tasks deleted successfully.'))
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to delete tasks.'))
          }
        },
      },
    ],
  })
}

async function submitBulkAssign() {
  if (!bulkAssignTargetUser.value) return
  bulkAssigning.value = true
  try {
    const res = await call('crm.api.daily_allocation.bulk_reassign_tasks', {
      tasks: selectedTaskIds.value,
      new_user: bulkAssignTargetUser.value,
    })
    toast.success(res.message || __('Tasks reassigned successfully.'))
    showAssignModal.value = false
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to reassign tasks.'))
  } finally {
    bulkAssigning.value = false
  }
}

function confirmClearAssignment() {
  $dialog({
    title: __('Clear Assignment'),
    message: __('Are you sure you want to clear assignment for {0} selected task(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Clear Assignment'),
        theme: 'red',
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_clear_task_assignments', {
              tasks: selectedTaskIds.value,
            })
            toast.success(res.message || __('Assignments cleared successfully.'))
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to clear assignments.'))
          }
        },
      },
    ],
  })
}

function confirmConvertToDeal() {
  $dialog({
    title: __('Convert to Deal'),
    message: __('Are you sure you want to convert {0} selected prospect(s) to deal(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Convert'),
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_convert_to_deal', {
              doctype: 'CRM Daily Allocation',
              names: selectedTaskIds.value,
            })
            if (res.converted > 0) {
              toast.success(__('Successfully converted {0} record(s) to deal(s).', [res.converted]))
            }
            if (res.errors && res.errors.length) {
              toast.warning(res.errors[0])
            }
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to convert to deal.'))
          }
        },
      },
    ],
  })
}

async function applyProspectStatus(statusName) {
  try {
    const res = await call('crm.api.daily_allocation.change_prospect_status', {
      doctype: 'CRM Daily Allocation',
      names: selectedTaskIds.value,
      status: statusName,
    })
    if (res.updated > 0) {
      toast.success(__('Updated CRM Lead status to {0} for {1} prospect(s)', [statusName, res.updated]))
    }
    if (res.skipped > 0) {
      toast.warning(__('Skipped {0} record(s) without linked CRM Lead', [res.skipped]))
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update status.'))
  }
}

async function applyTaskStatus(statusName) {
  try {
    const res = await call('crm.api.daily_allocation.bulk_update_tasks', {
      tasks: selectedTaskIds.value,
      status: statusName,
    })
    toast.success(res.message || __('Updated {0} task(s) to {1}.', [selectedTaskIds.value.length, statusName]))
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update status.'))
  }
}

async function loadTaskTemplates() {
  try {
    const list = await call('crm.api.daily_allocation.get_email_templates')
    taskEmailTemplates.value = list || []
  } catch (err) {
    console.error('Failed to load email templates:', err)
  }
}

async function applyTaskTemplate() {
  if (!selectedTaskTemplate.value) return
  try {
    const res = await call('crm.api.daily_allocation.render_email_template', {
      template_name: selectedTaskTemplate.value,
      contact: activeEmailTask.value?.contact || null,
    })
    if (res) {
      if (res.subject) taskEmailForm.subject = res.subject
      if (res.content) taskEmailForm.content = res.content
      taskEmailMode.value = 'preview'
      toast.success(__('Template applied'))
    }
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to apply template'))
  }
}

function openTaskEmail(task) {
  activeEmailTask.value = task
  taskEmailForm.recipient = task.email || ''
  taskEmailForm.subject = `Follow-up: ${task.contact_name}`
  taskEmailForm.content = `<p>Hi ${task.contact_name},</p><p>I am following up regarding our discussion.</p>`
  taskEmailForm.cc = ''
  taskEmailForm.bcc = ''
  taskEmailForm.templateName = ''
  taskEmailForm.isBranded = false
  showTaskEmailModal.value = true
}

async function submitTaskEmail() {
  if (!activeEmailTask.value) return
  taskEmailSending.value = true
  try {
    const res = await call('crm.api.daily_allocation.send_task_email', {
      task_name: activeEmailTask.value.name,
      recipient: taskEmailForm.recipient,
      subject: taskEmailForm.subject,
      content: taskEmailForm.content,
      cc: taskEmailForm.cc || null,
      bcc: taskEmailForm.bcc || null,
      template_name: taskEmailForm.templateName || null,
      is_branded: taskEmailForm.isBranded,
    })
    const isSent = res?.delivery_status === 'Sent' || res?.queue_status === 'Sent'
    toast.success(res?.message || (isSent ? __('Email sent successfully') : __('Email queued successfully')))
    showTaskEmailModal.value = false
    if (activeEmailTask.value.status === 'To Do') {
      activeEmailTask.value.status = 'In Progress'
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to send email'))
  } finally {
    taskEmailSending.value = false
  }
}

function openTaskCall(task) {
  activeCallTask.value = task
  taskCallForm.type = 'Outgoing'
  taskCallForm.status = 'Completed'
  taskCallForm.phone = task.mobile_no || ''
  taskCallForm.duration = '02:30'
  taskCallForm.note = ''
  showTaskCallModal.value = true
}

async function submitTaskCall() {
  if (!activeCallTask.value) return
  taskCallSaving.value = true
  try {
    let durSec = 0
    if (String(taskCallForm.duration).includes(':')) {
      const [m, s] = String(taskCallForm.duration).split(':').map((n) => parseInt(n) || 0)
      durSec = m * 60 + s
    } else {
      durSec = parseInt(taskCallForm.duration) || 0
    }

    await call('crm.api.daily_allocation.log_task_call', {
      task_name: activeCallTask.value.name,
      call_type: taskCallForm.type,
      phone: taskCallForm.phone,
      duration: durSec,
      status: taskCallForm.status,
      note: taskCallForm.note || null,
    })
    toast.success(__('Call logged successfully'))
    showTaskCallModal.value = false
    if (taskCallForm.status === 'Completed' && activeCallTask.value.status === 'To Do') {
      activeCallTask.value.status = 'In Progress'
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to log call'))
  } finally {
    taskCallSaving.value = false
  }
}

function onBulkEmailReload() {
  selectedTaskIds.value = []
  fetchTasks()
}

function handleDateModeChange() {
  if (dateFilterMode.value === 'today') {
    customDate.value = todayStr
  }
  fetchTasks()
}

async function fetchTasks(options = {}) {
  const append = options.append || false
  if (append) {
    if (loadingMore.value || loading.value) return
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    // Determine admin status
    if (!isAdminLoaded) {
      const summary = await call('crm.api.daily_allocation.get_daily_allocation_summary', {
        date: todayStr,
      })
      isAdmin.value = summary.is_admin
      isAdminLoaded = true

      if (isAdmin.value && !assignableUsers.value.length) {
        assignableUsers.value = await call('crm.api.daily_allocation.get_assignable_users')
      }
    }

    const params = {
      as_dict: 1,
      limit: pageSize.value,
      offset: append ? tasks.value.length : 0,
      status: currentStatus.value,
    }

    if (dateFilterMode.value === 'today') {
      params.date = todayStr
    } else if (dateFilterMode.value === 'custom' && customDate.value) {
      params.date = customDate.value
    }

    if (isAdmin.value && selectedUser.value !== 'all') {
      params.user = selectedUser.value
    }

    const q = searchQuery.value?.trim()
    if (q) {
      params.search = q
    }

    const res = await call('crm.api.daily_allocation.get_allocated_tasks', params)
    const rawTasks = Array.isArray(res) ? res : (res?.tasks || [])
    totalTasksCount.value = res?.total_count ?? rawTasks.length
    if (res?.status_counts) {
      serverStatusCounts.value = res.status_counts
    }

    if (Array.isArray(rawTasks)) {
      for (let i = 0; i < rawTasks.length; i++) {
        const t = rawTasks[i]
        t._displayCountry = (t.country && t.country !== 'Not Available') ? t.country : ''
        t._displayTimezone = (t.timezone && t.timezone !== 'Not Available') ? formatTimezone(t.timezone) : ''
        t._formattedCreation = t.creation ? formatDateTime(t.creation) : ''
        t._dataAge = t.creation ? formatDataAge(t.creation) : ''
        t._formattedModified = t.modified ? formatDateTime(t.modified) : ''
        t._timeAgo = t.modified ? formatTimeAgo(t.modified) : ''
      }
    }

    if (append) {
      const existingIds = new Set(tasks.value.map((t) => t.name))
      for (let i = 0; i < rawTasks.length; i++) {
        if (!existingIds.has(rawTasks[i].name)) {
          tasks.value.push(rawTasks[i])
          existingIds.add(rawTasks[i].name)
        }
      }
    } else {
      tasks.value = rawTasks || []
      selectedTaskSet.value = new Set()
    }
  } catch (error) {
    console.error('Error fetching tasks in MyTask:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function handleLoadMore() {
  if (loadingMore.value || loading.value) return
  if (tasks.value.length >= totalTasksCount.value) return
  fetchTasks({ append: true })
}

function getCountForStatus(statusVal) {
  return serverStatusCounts.value[statusVal] || 0
}

const filteredTasks = computed(() => {
  let list = tasks.value || []
  if (activeFilters.designation.size > 0) {
    list = list.filter((t) => activeFilters.designation.has((t.designation || '').trim()))
  }
  if (activeFilters.country.size > 0) {
    list = list.filter((t) => activeFilters.country.has((t.country || '').trim()))
  }
  if (activeFilters.timezone.size > 0) {
    list = list.filter((t) => activeFilters.timezone.has((t.timezone || '').trim()))
  }
  if (activeFilters.assigned_by.size > 0) {
    list = list.filter((t) => activeFilters.assigned_by.has((t.assigned_by || t.allocated_by || '').trim()))
  }
  if (activeFilters.last_updated.size > 0) {
    list = list.filter((t) => activeFilters.last_updated.has(getDateBucket(t.modified)))
  }
  if (activeFilters.data_age.size > 0) {
    list = list.filter((t) => activeFilters.data_age.has(getDateBucket(t.data_age_date || t.modified)))
  }
  return list
})

// Reset pagination when page size changes (20, 50, 100)
watch(pageSize, () => {
  fetchTasks()
})

// Reset pagination when status tab changes
watch(currentStatus, () => {
  fetchTasks()
})

// Debounce search query
let searchTimer = null
watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchTasks()
  }, 300)
})

// Checkbox selection computed & indeterminate state
const isAllSelected = computed(() => {
  const visible = filteredTasks.value
  if (!visible.length) return false
  const s = selectedTaskSet.value
  for (let i = 0; i < visible.length; i++) {
    if (!s.has(visible[i].name)) return false
  }
  return true
})

const isIndeterminate = computed(() => {
  const visible = filteredTasks.value
  if (!visible.length) return false
  const s = selectedTaskSet.value
  let sel = 0
  for (let i = 0; i < visible.length; i++) {
    if (s.has(visible[i].name)) {
      sel++
      if (sel < i + 1) return true
    } else if (sel > 0) {
      return true
    }
  }
  return false
})

watchEffect(() => {
  if (headerCheckboxRef.value) {
    headerCheckboxRef.value.indeterminate = isIndeterminate.value
  }
})

function toggleSelectAll(event) {
  const checked = event.target.checked
  const newSet = new Set(selectedTaskSet.value)
  const currentVisible = filteredTasks.value
  if (checked) {
    for (let i = 0; i < currentVisible.length; i++) {
      newSet.add(currentVisible[i].name)
    }
  } else {
    for (let i = 0; i < currentVisible.length; i++) {
      newSet.delete(currentVisible[i].name)
    }
  }
  selectedTaskSet.value = newSet
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'To Do':
      return 'bg-surface-gray-1 text-ink-gray-7 border-outline-gray-3'
    case 'In Progress':
      return 'bg-surface-blue-1 text-ink-blue-3 border-outline-blue-2'
    case 'Pending':
      return 'bg-surface-amber-1 text-ink-amber-3 border-outline-amber-2'
    case 'Callback':
      return 'bg-surface-purple-1 text-ink-purple-3 border-outline-purple-2'
    case 'Follow up':
      return 'bg-surface-teal-1 text-ink-teal-3 border-outline-teal-2'
    case 'Not Interested':
      return 'bg-surface-gray-2 text-ink-gray-6 border-outline-gray-3'
    default:
      return 'bg-surface-gray-1 text-ink-gray-7 border-outline-gray-2'
  }
}

async function handleStatusChange(task, newStatus) {
  const previousStatus = task.status
  task.status = newStatus
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: task.name,
      status: newStatus,
    })
    toast.success(__('Status updated to {0}', [newStatus]))
  } catch (error) {
    console.error('Error updating status:', error)
    task.status = previousStatus
    toast.error(__('Failed to update status'))
  }
}

function openEditModal(task) {
  selectedTask.value = task
  editForm.status = task.status || 'To Do'
  editForm.follow_up_date = task.follow_up_date || ''
  editForm.notes = task.notes || ''
  showEditModal.value = true
}

async function submitEdit() {
  if (!selectedTask.value) return
  saving.value = true
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: selectedTask.value.name,
      status: editForm.status,
      notes: editForm.notes,
      follow_up_date: editForm.follow_up_date,
    })
    selectedTask.value.status = editForm.status
    selectedTask.value.notes = editForm.notes
    selectedTask.value.follow_up_date = editForm.follow_up_date
    showEditModal.value = false
    toast.success(__('Task updated successfully'))
  } catch (error) {
    console.error('Save failed:', error)
    toast.error(__('Failed to save task update'))
  } finally {
    saving.value = false
  }
}

function onTasksRealtimeUpdate() {
  fetchTasks()
}

function handleClickOutside(e) {
  if (
    filterDropdownContainerRef.value &&
    !filterDropdownContainerRef.value.contains(e.target)
  ) {
    showFilterMenu.value = false
  }
}

onMounted(() => {
  fetchTasks()
  document.addEventListener('click', handleClickOutside)
  if ($socket) {
    $socket.on('crm_tasks_updated', onTasksRealtimeUpdate)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  if ($socket) {
    $socket.off('crm_tasks_updated', onTasksRealtimeUpdate)
  }
})
</script>
