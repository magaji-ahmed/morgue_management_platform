import { reactive } from "vue";

const BASE = import.meta.env.VITE_API_URL || "/api";
const CUR = import.meta.env.VITE_CURRENCY || "₦";

export const auth = reactive({
  token: localStorage.getItem("token"),
  user: JSON.parse(localStorage.getItem("user") || "null"),
});

export function setAuth(token, user) {
  auth.token = token; auth.user = user;
  token ? localStorage.setItem("token", token) : localStorage.removeItem("token");
  user ? localStorage.setItem("user", JSON.stringify(user)) : localStorage.removeItem("user");
}

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`;
  if (body) headers["Content-Type"] = "application/json";
  const res = await fetch(BASE + path, { method, headers, body: form || (body ? JSON.stringify(body) : undefined) });
  const data = await res.json().catch(() => null);
  if (res.status === 401 && auth.token) { setAuth(null, null); location.href = "/login"; }
  if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "That didn't work. Check the fields and try again.");
  return data;
}

// Server stores naive UTC, so add "Z" before parsing
export const fmt = (s) => (s ? new Date(s + "Z").toLocaleString() : "");
export const money = (n) => CUR + Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
