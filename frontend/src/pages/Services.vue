<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";
const items = ref([]), error = ref(""), ok = ref("");
const blank = () => ({ name: "", price: "" });
const form = ref(blank());
const load = async () => (items.value = await api("/services"));
async function run(fn) { error.value = ok.value = ""; try { await fn(); await load(); ok.value = "Saved."; } catch (e) { error.value = e.message; } }
const add = () => run(async () => { await api("/services", { method: "POST", body: { name: form.value.name, price: Number(form.value.price), active: true } }); form.value = blank(); });
const save = (s) => run(() => api(`/services/${s.id}`, { method: "PATCH", body: { name: s.name, price: Number(s.price), active: s.active } }));
const restore = (s) => { s.active = true; save(s); };
const remove = (s) => confirm(`Remove ${s.name}? Past records keep it on their receipts.`) && run(() => api(`/services/${s.id}`, { method: "DELETE" }));
onMounted(load);
</script>

<template>
    <section class="page">
        <h1>Services and prices</h1>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <p v-if="ok" class="ok">{{ ok }}</p>
        <form class="card form-grid" @submit.prevent="add">
            <label class="label">Service name <input class="field" v-model="form.name" required /></label>
            <label class="label">Price <input class="field" type="number" step="0.01" min="0" v-model="form.price"
                    required /></label>
            <button class="btn btn-primary">Add service</button>
        </form>
        <table class="grid-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Price</th>
                    <th>Status</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="s in items" :key="s.id">
                    <td><input class="cell-field" v-model="s.name" /></td>
                    <td><input class="cell-field" type="number" step="0.01" min="0" v-model="s.price" /></td>
                    <td><span class="badge" :class="{ 'badge-warn': !s.active }">{{ s.active ? "Available" : "Hidden"
                            }}</span></td>
                    <td class="acts">
                        <button class="btn" @click="save(s)">Save</button>
                        <button v-if="s.active" class="btn btn-danger" @click="remove(s)">Remove</button>
                        <button v-else class="btn" @click="restore(s)">Restore</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>
</template>