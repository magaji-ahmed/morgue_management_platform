<script setup>
import { reactive, watch } from "vue";
const props = defineProps({ initial: { type: Object, default: () => ({}) }, busy: Boolean, label: { type: String, default: "Save record" } });
const emit = defineEmits(["save"]);
const keys = ["full_name", "gender", "age", "date_of_death", "cause_of_death", "notes", "contact_name", "contact_phone", "contact_relation"];
const form = reactive(Object.fromEntries(keys.map((k) => [k, ""])));

watch(() => props.initial, (v) => keys.forEach((k) => (form[k] = v?.[k] ?? "")), { immediate: true, deep: true });

// Used by the scan flow: fills only the fields the scanner found
function fill(draft) { keys.forEach((k) => { if (draft[k] != null) form[k] = draft[k]; }); }
defineExpose({ fill });

function submit() {
  // Empty inputs become null so "unidentified" and "no contact yet" stay real database nulls
  emit("save", Object.fromEntries(keys.map((k) => [k, form[k] === "" || form[k] === null ? null : k === "age" ? Number(form[k]) : form[k]])));
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <fieldset>
      <legend>Deceased</legend>
      <label class="label span2">Full name <span class="hint">Leave blank if unidentified</span>
        <input class="field" v-model="form.full_name" />
      </label>
      <label class="label">Gender
        <select class="field" v-model="form.gender">
          <option value="">Not recorded</option>
          <option>Male</option>
          <option>Female</option>
        </select>
      </label>
      <label class="label">Age <input class="field" type="number" min="0" max="130" v-model="form.age" /></label>
      <label class="label">Date of death <input class="field" type="date" v-model="form.date_of_death" /></label>
      <label class="label span2">Cause of death <input class="field" v-model="form.cause_of_death" /></label>
      <label class="label span2">Notes <textarea class="field" rows="2" v-model="form.notes"></textarea></label>
    </fieldset>
    <fieldset>
      <legend>Contact person</legend>
      <p class="hint span2">Required before release. For an unidentified body, add it later.</p>
      <label class="label">Name <input class="field" v-model="form.contact_name" /></label>
      <label class="label">Phone <input class="field" v-model="form.contact_phone" /></label>
      <label class="label span2">Relationship <input class="field" v-model="form.contact_relation" /></label>
    </fieldset>
    <slot />
    <button class="btn btn-primary" :disabled="busy">{{ label }}</button>
  </form>
</template>

<style scoped>
.form {
  @apply space-y-5;
}

fieldset {
  @apply card grid gap-4 sm:grid-cols-2;
}

legend {
  @apply font-serif text-lg px-2;
}

.span2 {
  @apply sm:col-span-2;
}

.hint {
  @apply text-xs font-normal text-moss ml-1;
}
</style>
