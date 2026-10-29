<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { api, fmt, money } from "../api";
import BodyForm from "../components/BodyForm.vue";

const id = useRoute().params.id;
const b = ref(null), services = ref([]), logs = ref([]);
const pick = ref(""), amount = ref(""), note = ref(""), error = ref(""), saved = ref(false);
const print = () => window.print();

async function refreshLogs() { logs.value = await api(`/bodies/${id}/audit`); }
async function run(fn) {
  error.value = ""; saved.value = false;
  try { b.value = await fn(); await refreshLogs(); saved.value = true; }
  catch (e) { error.value = e.message; }
}
const save = (data) => run(() => api(`/bodies/${id}`, { method: "PATCH", body: data }));
const available = computed(() => services.value.filter((s) => !b.value.services.some((l) => l.service_id === s.id)));
const addService = () => run(async () => {
  const r = await api(`/bodies/${id}/services`, { method: "POST", body: { service_id: Number(pick.value) } });
  pick.value = ""; return r;
});
const toggleDone = (l) => run(() => api(`/bodies/${id}/services/${l.id}/done`, { method: "POST", body: { done: !l.done } }));
const removeLine = (l) => run(() => api(`/bodies/${id}/services/${l.id}`, { method: "DELETE" }));
const pay = () => run(async () => {
  const r = await api(`/bodies/${id}/payments`, { method: "POST", body: { amount: Number(amount.value), note: note.value || null } });
  amount.value = note.value = ""; return r;
});
const release = () => confirm("Release this body? This cannot be undone.") && run(() => api(`/bodies/${id}/release`, { method: "POST" }));

onMounted(async () => {
  services.value = (await api("/services")).filter((s) => s.active);
  b.value = await api(`/bodies/${id}`);
  await refreshLogs();
});
</script>

<template>
  <section v-if="b" class="page">
    <header class="no-print">
      <h1>{{ b.full_name || "Unidentified body" }}</h1>
      <span class="badge">{{ b.tag_no }} · {{ b.status }}</span>
    </header>
    <p v-if="error" class="error no-print" role="alert">{{ error }}</p>
    <p v-if="saved" class="ok no-print">Saved.</p>

    <div class="no-print">
      <BodyForm :initial="b" label="Save changes" @save="save" />
    </div>

    <div class="card no-print">
      <h2>Services</h2>
      <ul v-if="b.services.length" class="svc-list">
        <li v-for="l in b.services" :key="l.id" class="svc-item">
          <div>
            <strong>{{ l.name }}</strong> <span class="meta">{{ money(l.price) }}</span>
            <div class="meta">{{ l.done ? `Done by ${l.done_by}, ${fmt(l.done_at)}` : "Not done yet" }}</div>
          </div>
          <div v-if="b.status === 'stored'" class="acts">
            <button class="btn" @click="toggleDone(l)">{{ l.done ? "Mark undone" : "Mark done" }}</button>
            <button class="btn btn-danger" :disabled="l.done" @click="removeLine(l)">Remove</button>
          </div>
          <span v-else class="badge">{{ l.done ? "Done" : "Not done" }}</span>
        </li>
      </ul>
      <p v-else class="empty">No services chosen yet.</p>
      <form v-if="b.status === 'stored' && available.length" class="row" @submit.prevent="addService">
        <select class="field" v-model="pick" required>
          <option value="" disabled>Add a service</option>
          <option v-for="s in available" :key="s.id" :value="s.id">{{ s.name }} ({{ money(s.price) }})</option>
        </select>
        <button class="btn">Add</button>
      </form>
    </div>

    <div class="card receipt">
      <h2>Receipt {{ b.tag_no }}</h2>
      <p class="meta">{{ b.full_name || "Unidentified" }}, contact: {{ b.contact_name || "not yet recorded" }}<br />
        Admitted {{ fmt(b.admitted_at) }}<span v-if="b.released_at">, released {{ fmt(b.released_at) }}</span></p>
      <table class="grid-table">
        <tbody>
          <tr>
            <td>Storage, {{ b.receipt.days }} day(s) at {{ money(b.receipt.daily_rate) }}</td>
            <td class="num">{{ money(b.receipt.storage) }}</td>
          </tr>
          <tr v-for="s in b.services" :key="s.id">
            <td>{{ s.name }}</td>
            <td class="num">{{ money(s.price) }}</td>
          </tr>
          <tr class="strong">
            <td>Total</td>
            <td class="num">{{ money(b.receipt.total) }}</td>
          </tr>
          <tr v-for="p in b.payments" :key="p.id">
            <td>Paid {{ fmt(p.paid_at) }} {{ p.note }}</td>
            <td class="num">-{{ money(p.amount) }}</td>
          </tr>
          <tr class="strong">
            <td>Balance due</td>
            <td class="num">{{ money(b.receipt.balance) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="no-print actions">
        <form class="row" @submit.prevent="pay">
          <input class="field" type="number" step="0.01" min="0.01" v-model="amount" placeholder="Amount received"
            required />
          <input class="field" v-model="note" placeholder="Note (optional)" />
          <button class="btn">Record payment</button>
        </form>
        <button class="btn" @click="print">Print receipt</button>
        <button v-if="b.status === 'stored'" class="btn btn-danger" @click="release">Release body</button>
      </div>
    </div>

    <div class="card no-print">
      <h2>Activity log</h2>
      <table class="grid-table">
        <thead>
          <tr>
            <th>When</th>
            <th>Who</th>
            <th>What</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(l, i) in logs" :key="i">
            <td>{{ fmt(l.at) }}</td>
            <td>{{ l.username }}</td>
            <td>{{ l.action }}<br /><span class="meta">{{ l.detail }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page {
  @apply max-w-3xl space-y-5;
}

header {
  @apply flex flex-wrap items-center gap-3;
}

h1 {
  @apply text-3xl;
}

h2 {
  @apply text-xl mb-3;
}

ul {
  @apply mb-3 space-y-1 text-sm;
}

.row {
  @apply flex flex-wrap gap-2 items-center;
}

.row .field {
  @apply mt-0 w-auto flex-1 min-w-[10rem];
}

.actions {
  @apply mt-4 space-y-3;
}

.meta {
  @apply text-xs text-moss;
}

.num {
  @apply text-right whitespace-nowrap;
}

.strong td {
  @apply font-semibold;
}

.ok {
  @apply text-sm text-moss;
}
</style>
