<script setup lang="ts">
import { ref } from 'vue';
import { login, type CurrentUser } from '../api';

const emit = defineEmits<{
  login: [user: CurrentUser];
}>();

const email = ref('');
const password = ref('');
const error = ref('');
const isSubmitting = ref(false);

async function submitLogin() {
  error.value = '';
  isSubmitting.value = true;

  try {
    const user = await login(email.value, password.value);
    emit('login', user);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Login failed.';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section class="view login-view">
    <div class="view-header">
      <p class="eyebrow">Access</p>
      <h2>Login</h2>
      <p>Sign in with an admin or regular user account to manage rentals.</p>
    </div>

    <form class="form-grid" @submit.prevent="submitLogin">
      <label>
        Email
        <input v-model.trim="email" type="email" placeholder="admin@example.com" autocomplete="email" required />
      </label>
      <label>
        Password
        <input v-model="password" type="password" placeholder="Password" autocomplete="current-password" required />
      </label>
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Signing in...' : 'Sign in' }}
      </button>
      <p v-if="error" class="error-banner">{{ error }}</p>
    </form>
  </section>
</template>
