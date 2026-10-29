<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api, auth, setAuth } from "../api";
const router = useRouter();
const old_password = ref(""), new_password = ref(""), error = ref("");
async function submit() {
  error.value = "";
  try {
    const r = await api("/auth/change-password", { method: "POST", body: { old_password: old_password.value, new_password: new_password.value } });
    setAuth(r.token, r.user);
    old_password.value = new_password.value = "";
    router.push("/");
  } catch (e) { error.value = e.message; }
}
</script>

<template>
  <section class="page">
    <h1>My account</h1>
    <p class="who">{{ auth.user?.full_name }} ({{ auth.user?.username }}), {{ auth.user?.role }}</p>
    <p v-if="auth.user?.must_change_password" class="notice">Set a new password to start using the register.</p>
    <form class="card" @submit.prevent="submit">
      <h2>Change password</h2>
      <label class="label">Current password <input class="field" type="password" v-model="old_password" required /></label>
      <label class="label">New password <input class="field" type="password" minlength="8" v-model="new_password" required /></label>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <button class="btn btn-primary">Save new password</button>
    </form>
  </section>
</template>

<style scoped>
.page { @apply max-w-md space-y-4; }
h1 { @apply text-3xl; }
h2 { @apply text-xl; }
form { @apply space-y-4; }
.who { @apply text-moss text-sm; }
.notice { @apply rounded bg-brass/15 text-brass px-3 py-2 text-sm; }
</style>
