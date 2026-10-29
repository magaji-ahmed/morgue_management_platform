<script setup>
import { ref, watch, onMounted } from "vue";
import { api, fmt } from "../api";
const rows = ref([]), q = ref(""), loaded = ref(false);
let timer;
async function load() { rows.value = await api("/bodies?q=" + encodeURIComponent(q.value)); loaded.value = true; }
watch(q, () => { clearTimeout(timer); timer = setTimeout(load, 250); });
onMounted(load);
</script>

<template>
  <section class="page">
    <header>
      <h1>Bodies</h1>
      <RouterLink to="/bodies/new" class="btn btn-primary">Register a body</RouterLink>
    </header>
    <input class="field search" v-model="q" placeholder="Search by name, tag number or contact" aria-label="Search" />
    <table v-if="rows.length" class="grid-table">
      <thead><tr><th>Tag</th><th>Name</th><th>Admitted</th><th>Contact</th><th>Status</th></tr></thead>
      <tbody>
        <tr v-for="b in rows" :key="b.id">
          <td><RouterLink :to="`/bodies/${b.id}`" class="link">{{ b.tag_no }}</RouterLink></td>
          <td>{{ b.full_name || "Unidentified" }}</td>
          <td>{{ fmt(b.admitted_at) }}</td>
          <td><span v-if="b.contact_missing" class="badge badge-warn">Needed</span><span v-else>{{ b.contact_name }}</span></td>
          <td><span class="badge">{{ b.status }}</span></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="loaded" class="empty">No records match. Register a body to create the first one.</p>
  </section>
</template>

<style scoped>
.page { @apply space-y-5; }
header { @apply flex items-center justify-between gap-4; }
h1 { @apply text-3xl; }
.search { @apply max-w-md; }
.link { @apply underline underline-offset-2; }
.empty { @apply text-moss; }
</style>
