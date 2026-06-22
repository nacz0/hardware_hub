<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { config, getCurrentUser, getHealth, tokenStore, type CurrentUser, type HealthResult } from './api';
import AdminView from './views/AdminView.vue';
import AiAuditorView from './views/AiAuditorView.vue';
import DashboardView from './views/DashboardView.vue';
import LoginView from './views/LoginView.vue';

type ActiveView = 'dashboard' | 'audit' | 'admin';

const health = ref<HealthResult | null>(null);
const isCheckingHealth = ref(false);
const currentUser = ref<CurrentUser | null>(null);
const sessionError = ref('');
const isRestoringSession = ref(false);
const activeView = ref<ActiveView>('dashboard');
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
  activeView.value = 'dashboard';
}

function logout() {
  tokenStore.clear();
  currentUser.value = null;
  activeView.value = 'dashboard';
}
</script>

<template>
  <main v-if="!currentUser" class="login-shell">
    <p v-if="sessionError" class="error-banner">{{ sessionError }}</p>
    <p v-if="isRestoringSession" class="empty-state">Restoring session...</p>
    <LoginView v-else @login="handleLogin" />
  </main>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand-lockup">
        <span class="brand-mark" aria-hidden="true">HH</span>
        <h1>Hardware Manager</h1>
      </div>

      <nav class="nav-list" aria-label="Primary">
        <button
          class="nav-button"
          :class="{ active: activeView === 'dashboard' }"
          type="button"
          @click="activeView = 'dashboard'"
        >
          Hardware List
        </button>
        <button
          v-if="isAdmin"
          class="nav-button"
          :class="{ active: activeView === 'audit' }"
          type="button"
          @click="activeView = 'audit'"
        >
          AI Auditor
        </button>
        <button
          v-if="isAdmin"
          class="nav-button"
          :class="{ active: activeView === 'admin' }"
          type="button"
          @click="activeView = 'admin'"
        >
          Admin Panel
        </button>
      </nav>

      <div class="sidebar-spacer"></div>

      <div class="session-card">
        <span class="label">Signed in</span>
        <strong>{{ currentUser.email }}</strong>
        <span class="role-pill">{{ currentUser.role }}</span>
      </div>

      <button class="logout-button" type="button" @click="logout">Log out</button>
    </aside>

    <main class="main-content">
      <p v-if="sessionError" class="error-banner">{{ sessionError }}</p>

      <DashboardView v-if="activeView === 'dashboard'" :current-user="currentUser" />
      <AiAuditorView v-else-if="activeView === 'audit' && isAdmin" />
      <AdminView v-else-if="activeView === 'admin' && isAdmin" />

      <section class="status-bar compact">
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
    </main>
  </div>
</template>
