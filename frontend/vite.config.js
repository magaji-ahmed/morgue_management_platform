import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
// In dev, /api is forwarded to FastAPI so the browser sees one origin (no CORS fuss).
export default defineConfig({ plugins: [vue()], server: { proxy: { "/api": "http://localhost:8000" } } });
