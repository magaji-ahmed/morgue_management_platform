<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api, setAuth } from "../api";
const router = useRouter();
const username = ref(""), password = ref(""), error = ref(""), busy = ref(false);
async function submit() {
  busy.value = true; error.value = "";
  try {
    const r = await api("/auth/login", { method: "POST", body: { username: username.value, password: password.value } });
    setAuth(r.token, r.user);
    router.push(r.user.must_change_password ? "/account" : "/");
  } catch (e) { error.value = e.message; } finally { busy.value = false; }
}
</script>

<template>
  <div class="login">
    <form class="card panel" @submit.prevent="submit">
      <h1>Mortuary register</h1>
      <p class="hint">Sign in with the account an administrator created for you.</p>
      <label class="label">Username <input class="field" v-model="username" autocomplete="username" required /></label>
      <label class="label">Password <input class="field" type="password" v-model="password"
          autocomplete="current-password" required /></label>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <button class="btn btn-primary" :disabled="busy">Sign in</button>
    </form>
  </div>
</template>

<style scoped>
.login {
  @apply min-h-[80vh] grid place-items-center;
}

.panel {
  @apply w-full max-w-sm space-y-4 p-7;
}

h1 {
  @apply text-3xl;
}

.hint {
  @apply text-sm text-moss;
}
</style>
