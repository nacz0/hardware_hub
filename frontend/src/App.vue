<script setup lang="ts">
import { computed, ref } from 'vue';
import { config, getHealth, type HealthResult } from './api';
import AdminView from './views/AdminView.vue';
import AiAuditorView from './views/AiAuditorView.vue';
import DashboardView from './views/DashboardView.vue';
import LoginView from './views/LoginView.vue';

type ViewKey = 'login' | 'dashboard' | 'admin' | 'ai-auditor';

const activeView = ref<ViewKey>('login');
const health = ref<HealthResult | null>(null);
const isCheckingHealth = ref(false);

const views: Array<{ key: ViewKey; label: string }> = [
  { key: 'login', label: 'Login' },
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'admin', label: 'Admin' },
  { key: 'ai-auditor', label: 'AI Auditor' },
];

const activeComponent = computed(() => {
  const components = {
    login: LoginView,
    dashboard: DashboardView,
    admin: AdminView,
    'ai-auditor': AiAuditorView,
  };

  return components[activeView.value];
});

async function checkHealth() {
  isCheckingHealth.value = true;
  health.value = await getHealth();
  isCheckingHealth.value = false;
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Hardware Hub</p>
        <h1>Operations Console</h1>
      </div>

      <nav class="nav-list" aria-label="Main views">
        <button
          v-for="view in views"
          :key="view.key"
          class="nav-button"
          :class="{ active: activeView === view.key }"
          type="button"
          @click="activeView = view.key"
        >
          {{ view.label }}
        </button>
      </nav>
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

      <component :is="activeComponent" />
    </main>
  </div>
</template>
