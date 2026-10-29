<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api, money } from "../api";
import BodyForm from "../components/BodyForm.vue";
const router = useRouter(), formRef = ref(), busy = ref(false), error = ref(""), scanned = ref(false);
const services = ref([]), chosen = ref([]);
onMounted(async () => (services.value = (await api("/services")).filter((s) => s.active)));

async function scan(e) {
  const file = e.target.files[0]; if (!file) return;
  error.value = "";
  const form = new FormData(); form.append("file", file);
  try { formRef.value.fill((await api("/bodies/scan", { method: "POST", form })).draft); scanned.value = true; }
  catch (err) { error.value = err.message; }
}

async function save(data) {
  busy.value = true; error.value = "";
  try { router.push(`/bodies/${(await api("/bodies", { method: "POST", body: data, services_ids: chosen.value })).id}`); }
  catch (e) { error.value = e.message; busy.value = false; }
}
</script>

<template>
  <section class="page">
    <h1>Register a body</h1>
    <div class="card scan">
      <label class="label">Scan the paper form
        <input class="field" type="file" accept="image/*,application/pdf" @change="scan" />
      </label>
      <p v-if="scanned" class="check">Scanner results are a draft. Check every field before saving.</p>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <BodyForm ref="formRef" :busy="busy" label="Save body record" @save="save">
      <div class="card">
        <h2>Services requested</h2>
        <p class="hint">Tick what the family wants. Staff mark each one done later.</p>
        <label v-for="s in services" :key="s.id" class="check-row">
          <input type="checkbox" :value="s.id" v-model="chosen" /> {{ s.name }} <span class="meta">{{ money(s.price)
            }}</span>
        </label>
      </div>
    </BodyForm>
  </section>
</template>

<style scoped>
.page {
  @apply max-w-2xl space-y-5;
}

h1 {
  @apply text-3xl;
}

.scan {
  @apply space-y-2;
}

.check {
  @apply text-sm rounded bg-brass/15 text-brass px-3 py-2;
}
</style>
