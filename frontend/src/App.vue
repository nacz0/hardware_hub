<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { config, getCurrentUser, getHealth, tokenStore, type CurrentUser, type HealthResult } from './api';
import AdminView from './views/AdminView.vue';
import AiAuditorView from './views/AiAuditorView.vue';
import DashboardView from './views/DashboardView.vue';
import LoginView from './views/LoginView.vue';

const health = ref<HealthResult | null>(null);
const isCheckingHealth = ref(false);
const currentUser = ref<CurrentUser | null>(null);
const sessionError = ref('');
const isRestoringSession = ref(false);
const isAdmin = computed(() => currentUser.value?.role === 'admin');

onMounted(async () => {
  const token = tokenStore.get();
  if (!token) {
    return;
  }

  isRestoringSession.value = true;
  try {
    currentUser.value = await getCurrentUser(token);
  } catch (error) {
    tokenStore.clear();
    sessionError.value =
      error instanceof Error ? error.message : 'Stored session could not be restored.';
  } finally {
    isRestoringSession.value = false;
  }
});

async function checkHealth() {
  isCheckingHealth.value = true;
  health.value = await getHealth();
  isCheckingHealth.value = false;
}

function handleLogin(user: CurrentUser) {
  sessionError.value = '';
  currentUser.value = user;
}

function logout() {
  tokenStore.clear();
  currentUser.value = null;
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Hardware Hub</p>
        <h1>Operations Console</h1>
      </div>

      <div v-if="currentUser" class="session-card">
        <span class="label">Signed in</span>
        <strong>{{ currentUser.email }}</strong>
        <span class="role-pill">{{ currentUser.role }}</span>
        <button class="secondary-button" type="button" @click="logout">Log out</button>
      </div>
    </aside>

    <main class="main-content">
      <section class="status-bar">
        <div>
          <span class="label">API</span>
          <code>{{ config.apiUrl }}</code>
        </div>
        <button class="secondary-button" type="button" :disabled="isCheckingHealth" @click="checkHealth">
          {{ isCheckingHealth ? 'Checking...' : 'Check /health' }}
        </button>
      </section>

      <section v-if="health" class="health-panel" :class="{ healthy: health.ok, unhealthy: !health.ok }">
        <strong>{{ health.ok ? 'Backend reachable' : 'Backend unavailable' }}</strong>
        <span v-if="health.status">Status {{ health.status }}</span>
        <span v-else-if="health.error">{{ health.error }}</span>
        <pre v-if="health.body">{{ health.body }}</pre>
      </section>

      <p v-if="sessionError" class="error-banner">{{ sessionError }}</p>
      <p v-if="isRestoringSession" class="empty-state">Restoring session...</p>

      <template v-else-if="currentUser">
        <DashboardView :current-user="currentUser" />
        <AiAuditorView v-if="isAdmin" />
        <AdminView v-if="isAdmin" />
      </template>
      <LoginView v-else @login="handleLogin" />
    </main>
  </div>
</template>
