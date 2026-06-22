<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  createHardware,
  createUserAccount,
  deleteHardware,
  getHardware,
  markHardwareRepair,
  type CreateHardwareInput,
  type CreateUserInput,
  type CurrentUser,
  type HardwareItem,
} from '../api';

type HardwareForm = {
  externalId: string;
  name: string;
  brand: string;
  purchaseDate: string;
  status: CreateHardwareInput['status'];
  assignedTo: string;
  notes: string;
  history: string;
};

const userForm = ref<CreateUserInput>({
  email: '',
  password: '',
  role: 'user',
});

const hardwareForm = ref<HardwareForm>({
  externalId: '',
  name: '',
  brand: '',
  purchaseDate: '',
  status: 'Available',
  assignedTo: '',
  notes: '',
  history: '',
});

const hardware = ref<HardwareItem[]>([]);
const createdUsers = ref<CurrentUser[]>([]);
const userError = ref('');
const userSuccess = ref('');
const hardwareError = ref('');
const hardwareSuccess = ref('');
const isCreatingUser = ref(false);
const isAddingHardware = ref(false);
const isLoadingHardware = ref(false);
const actionId = ref<number | null>(null);

const sortedHardware = computed(() =>
  hardware.value.slice().sort((left, right) => left.name.localeCompare(right.name)),
);

onMounted(() => {
  void loadHardware();
});

async function loadHardware() {
  hardwareError.value = '';
  isLoadingHardware.value = true;

  try {
    hardware.value = await getHardware();
  } catch (caught) {
    hardwareError.value = caught instanceof Error ? caught.message : 'Hardware list could not be loaded.';
  } finally {
    isLoadingHardware.value = false;
  }
}

async function submitUser() {
  userError.value = '';
  userSuccess.value = '';
  isCreatingUser.value = true;

  try {
    const created = await createUserAccount({
      email: userForm.value.email,
      password: userForm.value.password,
      role: userForm.value.role,
    });
    createdUsers.value = [created, ...createdUsers.value.filter((user) => user.id !== created.id)];
    userForm.value = { email: '', password: '', role: 'user' };
    userSuccess.value = `Created ${created.email}.`;
  } catch (caught) {
    userError.value = caught instanceof Error ? caught.message : 'User account could not be created.';
  } finally {
    isCreatingUser.value = false;
  }
}

async function submitHardware() {
  hardwareError.value = '';
  hardwareSuccess.value = '';
  isAddingHardware.value = true;

  try {
    const created = await createHardware(toHardwareInput());
    hardwareForm.value = {
      externalId: '',
      name: '',
      brand: '',
      purchaseDate: '',
      status: 'Available',
      assignedTo: '',
      notes: '',
      history: '',
    };
    hardwareSuccess.value = `Added ${created.name}.`;
    await loadHardware();
  } catch (caught) {
    hardwareError.value = caught instanceof Error ? caught.message : 'Hardware could not be added.';
  } finally {
    isAddingHardware.value = false;
  }
}

async function runHardwareAction(item: HardwareItem, action: 'repair' | 'delete') {
  hardwareError.value = '';
  hardwareSuccess.value = '';

  if (action === 'delete' && !window.confirm(`Delete ${item.name}?`)) {
    return;
  }

  actionId.value = item.id;

  try {
    if (action === 'repair') {
      await markHardwareRepair(item.id);
      hardwareSuccess.value = `Marked ${item.name} as Repair.`;
    } else {
      await deleteHardware(item.id);
      hardwareSuccess.value = `Deleted ${item.name}.`;
    }

    await loadHardware();
  } catch (caught) {
    hardwareError.value = caught instanceof Error ? caught.message : 'Hardware action failed.';
  } finally {
    actionId.value = null;
  }
}

function toHardwareInput(): CreateHardwareInput {
  return {
    externalId: optionalNumber(hardwareForm.value.externalId),
    name: hardwareForm.value.name,
    brand: optionalText(hardwareForm.value.brand),
    purchaseDate: optionalText(hardwareForm.value.purchaseDate),
    status: hardwareForm.value.status,
    assignedTo: optionalText(hardwareForm.value.assignedTo),
    notes: optionalText(hardwareForm.value.notes),
    history: optionalText(hardwareForm.value.history),
  };
}

function optionalText(value: string): string | null {
  return value.trim() || null;
}

function optionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatText(value?: string | number | null): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  return String(value);
}
</script>

<template>
  <section class="view admin-view">
    <div class="view-header">
      <p class="eyebrow">Control</p>
      <h2>Admin</h2>
      <p>Create accounts and manage hardware records.</p>
    </div>

    <div class="admin-layout">
      <form class="admin-panel" @submit.prevent="submitUser">
        <div>
          <h3>Create user account</h3>
          <p class="panel-note">The backend enforces admin authorization for this action.</p>
        </div>

        <label>
          Email
          <input v-model.trim="userForm.email" type="email" autocomplete="off" required />
        </label>
        <label>
          Password
          <input v-model="userForm.password" type="password" minlength="8" maxlength="72" autocomplete="new-password" required />
        </label>
        <label>
          Role
          <select v-model="userForm.role">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <button type="submit" :disabled="isCreatingUser">
          {{ isCreatingUser ? 'Creating...' : 'Create user' }}
        </button>

        <p v-if="userError" class="error-banner">{{ userError }}</p>
        <p v-if="userSuccess" class="success-banner">{{ userSuccess }}</p>

        <div v-if="createdUsers.length" class="created-users">
          <span class="label">Created this session</span>
          <ul>
            <li v-for="user in createdUsers" :key="user.id">
              <strong>{{ user.email }}</strong>
              <span class="role-pill">{{ user.role }}</span>
            </li>
          </ul>
        </div>
      </form>

      <form class="admin-panel" @submit.prevent="submitHardware">
        <div>
          <h3>Add hardware</h3>
          <p class="panel-note">Use the assignment fields only.</p>
        </div>

        <label>
          Name
          <input v-model.trim="hardwareForm.name" type="text" required />
        </label>
        <label>
          Brand
          <input v-model.trim="hardwareForm.brand" type="text" />
        </label>
        <label>
          Purchase date
          <input v-model.trim="hardwareForm.purchaseDate" type="text" placeholder="YYYY-MM-DD" />
        </label>
        <label>
          Status
          <select v-model="hardwareForm.status">
            <option value="Available">Available</option>
            <option value="In Use">In Use</option>
            <option value="Repair">Repair</option>
          </select>
        </label>
        <label>
          Assigned to
          <input v-model.trim="hardwareForm.assignedTo" type="email" />
        </label>
        <label>
          Source ID
          <input v-model.trim="hardwareForm.externalId" type="number" inputmode="numeric" />
        </label>
        <label>
          Notes
          <textarea v-model.trim="hardwareForm.notes" rows="3"></textarea>
        </label>
        <label>
          History
          <textarea v-model.trim="hardwareForm.history" rows="3"></textarea>
        </label>

        <button type="submit" :disabled="isAddingHardware">
          {{ isAddingHardware ? 'Adding...' : 'Add hardware' }}
        </button>
      </form>
    </div>

    <div class="admin-table-header">
      <div>
        <h3>Hardware management</h3>
        <p class="panel-note">{{ hardware.length }} records loaded.</p>
      </div>
      <button class="secondary-button" type="button" :disabled="isLoadingHardware" @click="loadHardware">
        {{ isLoadingHardware ? 'Loading...' : 'Refresh hardware' }}
      </button>
    </div>

    <p v-if="hardwareError" class="error-banner">{{ hardwareError }}</p>
    <p v-if="hardwareSuccess" class="success-banner">{{ hardwareSuccess }}</p>
    <p v-if="isLoadingHardware && !hardware.length" class="empty-state">Loading hardware...</p>

    <div v-else class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Brand</th>
            <th>Status</th>
            <th>Assigned to</th>
            <th>Source ID</th>
            <th>Admin actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedHardware" :key="item.id">
            <td data-label="Name">
              <strong>{{ item.name }}</strong>
            </td>
            <td data-label="Brand">{{ formatText(item.brand) }}</td>
            <td data-label="Status">
              <span class="status-pill" :class="`status-${(item.status || 'unknown').toLowerCase().replace(/ /g, '-')}`">
                {{ formatText(item.status) }}
              </span>
            </td>
            <td data-label="Assigned to">{{ formatText(item.assignedTo) }}</td>
            <td data-label="Source ID">{{ formatText(item.externalId) }}</td>
            <td data-label="Admin actions">
              <div class="row-actions">
                <button
                  class="secondary-button"
                  type="button"
                  :disabled="item.status === 'Repair' || actionId === item.id"
                  @click="runHardwareAction(item, 'repair')"
                >
                  {{ actionId === item.id ? 'Working...' : 'Mark Repair' }}
                </button>
                <button
                  class="danger-button"
                  type="button"
                  :disabled="actionId === item.id"
                  @click="runHardwareAction(item, 'delete')"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="!sortedHardware.length" class="empty-state">No hardware records loaded.</p>
    </div>
  </section>
</template>
