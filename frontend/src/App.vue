<script setup>
import { RouterLink, RouterView, useRouter } from "vue-router";
import { auth, setAuth } from "./api";
const router = useRouter();
function signOut() { setAuth(null, null); router.push("/login"); }
</script>

<template>
  <div class="shell">
    <aside v-if="auth.token" class="side no-print">
      <div class="brand">Mortuary register</div>
      <nav>
        <RouterLink to="/">Bodies</RouterLink>
        <RouterLink to="/bodies/new">Register a body</RouterLink>
        <RouterLink v-if="auth.user?.role === 'admin'" to="/services">Services and prices</RouterLink>
        <RouterLink v-if="auth.user?.role === 'admin'" to="/users">Staff accounts</RouterLink>
        <RouterLink to="/account">My account</RouterLink>
      </nav>
      <div class="who">
        <span>{{ auth.user?.full_name }}</span>
        <button @click="signOut">Sign out</button>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.shell {
  @apply min-h-screen md:flex;
}

.side {
  @apply bg-ink text-mist p-5 flex flex-wrap items-center gap-x-6 gap-y-3 sticky top-0 z-10 md:w-60 md:h-screen md:self-start md:overflow-y-auto md:flex-col md:items-stretch md:justify-start md:shrink-0;
}

.brand {
  @apply font-serif text-xl text-paper;
}

nav {
  @apply flex flex-wrap gap-4 md:flex-col md:gap-1 md:mt-6 md:flex-1;
}

nav a {
  @apply rounded px-2 py-1.5 text-sm hover:bg-white/10;
}

nav a.router-link-exact-active {
  @apply bg-white/15 text-paper;
}

.who {
  @apply text-sm flex items-center gap-3 md:flex-col md:items-start md:gap-1;
}

.who button {
  @apply underline text-mist/80 hover:text-paper;
}

.content {
  @apply flex-1 p-5 md:p-10 max-w-5xl;
}
</style>
