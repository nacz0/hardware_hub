<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  getHardware,
  rentHardware,
  returnHardware,
  type CurrentUser,
  type HardwareItem,
} from '../api';

const props = defineProps<{
  currentUser: CurrentUser;
}>();

type SortField = 'name' | 'purchaseDate';
type SortDirection = 'asc' | 'desc';

const isoDatePattern = /^(\d{4})-(\d{2})-(\d{2})$/;

const hardware = ref<HardwareItem[]>([]);
const error = ref('');
const isLoading = ref(false);
const actionId = ref<number | null>(null);
const statusFilter = ref('all');
const brandFilter = ref('all');
const searchText = ref('');
const sortField = ref<SortField>('name');
const sortDirection = ref<SortDirection>('asc');

const statuses = computed(() =>
  Array.from(new Set(hardware.value.map((item) => item.status || 'Unknown'))).sort((a, b) =>
    a.localeCompare(b),
  ),
);

const brands = computed(() =>
  Array.from(new Set(hardware.value.map((item) => item.brand?.trim()).filter(Boolean) as string[])).sort(
    (a, b) => a.localeCompare(b),
  ),
);

const filteredHardware = computed(() => {
  const search = searchText.value.trim().toLowerCase();

  return hardware.value
    .filter((item) => {
      const statusMatches = statusFilter.value === 'all' || item.status === statusFilter.value;
      const brandMatches = brandFilter.value === 'all' || item.brand === brandFilter.value;
      const searchMatches =
        !search ||
        [item.name, item.brand, item.assignedTo]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(search));

      return statusMatches && brandMatches && searchMatches;
    })
    .slice()
    .sort((left, right) => {
      const direction = sortDirection.value === 'asc' ? 1 : -1;

      if (sortField.value === 'purchaseDate') {
        return comparePurchaseDate(left, right, direction);
      }

      return left.name.localeCompare(right.name) * direction;
    });
});

const totalCount = computed(() => hardware.value.length);
const availableCount = computed(() => hardware.value.filter((item) => item.status === 'Available').length);
const inUseCount = computed(() => hardware.value.filter((item) => item.status === 'In Use').length);

onMounted(() => {
  void loadHardware();
});

async function loadHardware() {
  error.value = '';
  isLoading.value = true;

  try {
    hardware.value = await getHardware();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Hardware list could not be loaded.';
  } finally {
    isLoading.value = false;
  }
}

async function runHardwareAction(item: HardwareItem, action: 'rent' | 'return') {
  error.value = '';
  actionId.value = item.id;

  try {
    if (action === 'rent') {
      await rentHardware(item.id);
    } else {
      await returnHardware(item.id);
    }

    hardware.value = await getHardware();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Hardware action failed.';
  } finally {
    actionId.value = null;
  }
}

function comparePurchaseDate(left: HardwareItem, right: HardwareItem, direction: number): number {
  const leftDate = getDateSortValue(left.purchaseDate);
  const rightDate = getDateSortValue(right.purchaseDate);

  if (leftDate.isValid !== rightDate.isValid) {
    return leftDate.isValid ? -1 : 1;
  }

  if (leftDate.time === rightDate.time) {
    return left.name.localeCompare(right.name);
  }

  return (leftDate.time - rightDate.time) * direction;
}

function getDateSortValue(value?: string | null): { isValid: boolean; time: number } {
  const match = value?.trim().match(isoDatePattern);
  if (!match) {
    return { isValid: false, time: 0 };
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  const isValid =
    parsed.getUTCFullYear() === year &&
    parsed.getUTCMonth() === month - 1 &&
    parsed.getUTCDate() === day;

  return isValid ? { isValid: true, time: parsed.getTime() } : { isValid: false, time: 0 };
}

function canReturn(item: HardwareItem): boolean {
  return item.status === 'In Use' && Boolean(item.assignedTo?.trim());
}

function formatText(value?: string | null): string {
  return value?.trim() || '-';
}
</script>

<template>
  <section class="view dashboard-view">
    <div class="page-heading">
      <div>
        <h2>Hardware List</h2>
        <p>{{ totalCount }} devices tracked for {{ props.currentUser.email }}.</p>
      </div>
      <button class="secondary-button" type="button" :disabled="isLoading" @click="loadHardware">
        {{ isLoading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <div class="metric-grid">
      <article class="metric">
        <span>Total devices</span>
        <strong>{{ totalCount }}</strong>
      </article>
      <article class="metric">
        <span>Available</span>
        <strong>{{ availableCount }}</strong>
      </article>
      <article class="metric">
        <span>In use</span>
        <strong>{{ inUseCount }}</strong>
      </article>
    </div>

    <div class="toolbar dashboard-toolbar" aria-label="Hardware filters">
      <label>
        Search
        <input v-model.trim="searchText" type="search" placeholder="Name, brand, or assignee" />
      </label>
      <label>
        Status
        <select v-model="statusFilter">
          <option value="all">All statuses</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <label>
        Brand
        <select v-model="brandFilter">
          <option value="all">All brands</option>
          <option v-for="brand in brands" :key="brand" :value="brand">{{ brand }}</option>
        </select>
      </label>
      <label>
        Sort by
        <select v-model="sortField">
          <option value="name">Name</option>
          <option value="purchaseDate">Purchase date</option>
        </select>
      </label>
      <label>
        Direction
        <select v-model="sortDirection">
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
      </label>
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>
    <p v-if="isLoading && !hardware.length" class="empty-state">Loading hardware...</p>

    <div v-else class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Brand</th>
            <th>Purchase date</th>
            <th>Status</th>
            <th>Assigned to</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredHardware" :key="item.id">
            <td data-label="Name">
              <strong>{{ item.name }}</strong>
            </td>
            <td data-label="Brand">{{ formatText(item.brand) }}</td>
            <td data-label="Purchase date">{{ formatText(item.purchaseDate) }}</td>
            <td data-label="Status">
              <span class="status-pill" :class="`status-${(item.status || 'unknown').toLowerCase().replace(/ /g, '-')}`">
                {{ formatText(item.status) }}
              </span>
            </td>
            <td data-label="Assigned to">{{ formatText(item.assignedTo) }}</td>
            <td data-label="Actions">
              <div class="row-actions">
                <button
                  type="button"
                  :disabled="item.status !== 'Available' || actionId === item.id"
                  @click="runHardwareAction(item, 'rent')"
                >
                  {{ actionId === item.id ? 'Working...' : 'Rent' }}
                </button>
                <button
                  class="secondary-button"
                  type="button"
                  :disabled="!canReturn(item) || actionId === item.id"
                  @click="runHardwareAction(item, 'return')"
                >
                  Return
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="!filteredHardware.length" class="empty-state">No hardware matches the current filters.</p>
    </div>
  </section>
</template>
