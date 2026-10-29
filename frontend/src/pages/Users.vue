<script setup>
import { ref, onMounted } from "vue";
import { api, auth, fmt } from "../api";
const users = ref([]), error = ref("");
const blank = () => ({ username: "", full_name: "", password: "", role: "staff" });
const form = ref(blank());
const load = async () => (users.value = await api("/users"));
async function run(fn) { error.value = ""; try { await fn(); await load(); } catch (e) { error.value = e.message; } }
const create = () => run(async () => { await api("/users", { method: "POST", body: form.value }); form.value = blank(); });
const setStatus = (u, status) => run(() => api(`/users/${u.id}`, { method: "PATCH", body: { status } }));
const reset = (u) => { const password = prompt(`Temporary password for ${u.username} (min 8 characters):`); if (password) run(() => api(`/users/${u.id}`, { method: "PATCH", body: { password } })); };
const remove = (u) => confirm(`Delete ${u.username}? Their past activity stays in the logs.`) && run(() => api(`/users/${u.id}`, { method: "DELETE" }));
onMounted(load);
</script>

<template>
  <section class="page">
    <h1>Staff accounts</h1>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <form class="card grid" @submit.prevent="create">
      <label class="label">Username <input class="field" v-model="form.username" required minlength="3" /></label>
      <label class="label">Full name <input class="field" v-model="form.full_name" required /></label>
      <label class="label">Temporary password <input class="field" v-model="form.password" required
          minlength="8" /></label>
      <label class="label">Role <select class="field" v-model="form.role">
          <option value="staff">Staff</option>
          <option value="admin">Admin</option>
        </select></label>
      <button class="btn btn-primary">Create account</button>
    </form>
    <table class="grid-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Role</th>
          <th>Status</th>
          <th>Created</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.full_name }}<br /><span class="meta">{{ u.username }}</span></td>
          <td>{{ u.role }}</td>
          <td><span class="badge" :class="{ 'badge-warn': u.status !== 'active' }">{{ u.status }}</span></td>
          <td>{{ fmt(u.created_at) }}</td>
          <td class="acts" v-if="u.status !== 'deleted' && u.id !== auth.user.id">
            <button class="btn" v-if="u.status === 'active'" @click="setStatus(u, 'suspended')">Suspend</button>
            <button class="btn" v-else @click="setStatus(u, 'active')">Reactivate</button>
            <button class="btn" @click="reset(u)">Reset password</button>
            <button class="btn btn-danger" @click="remove(u)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.page {
  @apply space-y-5;
}

h1 {
  @apply text-3xl;
}

/* 💻 Changed name to fix the circular dependency loop */
.page-grid {
  @apply grid gap-4 sm:grid-cols-2 items-end;
}

.acts {
  @apply flex flex-wrap gap-2;
}

.meta {
  @apply text-xs text-moss;
}
</style>
