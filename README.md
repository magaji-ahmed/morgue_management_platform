# Mortuary register

Body registration, services, billing/receipts, staff accounts and a full audit trail.

- **Backend:** FastAPI + SQLAlchemy (`backend/`)
- **Frontend:** Vue 3 + Vite + Tailwind 3 (`frontend/`). Shared styles are in `src/styles/main.css`; each page keeps its own `<style scoped>`.
- **Database:** Supabase Postgres
- **First login:** the admin from `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`). You are forced to change the password on first sign-in.

## 1. Supabase (do this first, every deployment needs it)
1. Create a project at supabase.com. Save the database password.
2. Project Settings > Database > Connection string > **Session pooler** (port 5432). Copy it into `DATABASE_URL`, with `?sslmode=require` at the end.
   *Why the pooler:* the direct host is IPv6-only on many plans, so Render and many VPSes can't reach it.
3. Start the backend once. It creates the tables, turns on row-level security, makes `audit_log` append-only, and seeds the admin and three starter services.
   *Why RLS:* Supabase exposes tables over a public REST API. RLS with no policies blocks that route; the backend connects as the owner and is unaffected.
4. Never put the Supabase anon/service keys in the frontend. The browser only ever talks to FastAPI.

## 2. Run locally
```bash
cp .env.example .env          # fill DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD
docker compose up --build     # app at http://localhost:8080, API docs at :8000/docs
```
Without Docker (leave `DATABASE_URL` unset to use a local SQLite file):
```bash
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload
cd ../frontend && npm install && npm run dev     # http://localhost:5173, /api is proxied to :8000
```

## 3. Production: Render (API) + Vercel (frontend) + Supabase (DB)
**Render (backend)**
1. New > Web Service > connect the repo. Root directory `backend`, runtime **Docker**.
2. Environment: `DATABASE_URL`, `SECRET_KEY` (`openssl rand -hex 32`), `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DAILY_RATE`, and `CORS_ORIGINS=https://YOUR-APP.vercel.app`.
   *Why CORS_ORIGINS:* the browser blocks calls from your Vercel domain unless the API names it.
3. Health check path: `/api/health`. Note the URL, e.g. `https://mortuary-api.onrender.com`.
4. Free instances sleep after inactivity; use a paid instance for a system staff rely on.

**Vercel (frontend)**
1. New Project > same repo. Root directory `frontend`, framework Vite.
2. Environment variable: `VITE_API_URL=https://mortuary-api.onrender.com/api` (optional: `VITE_CURRENCY`).
   *Why:* Vite bakes this in at build time, so redeploy after changing it.
3. `vercel.json` already rewrites all paths to `index.html` so refreshing `/bodies/3` works.

## 4. Production: VPS (Ubuntu) with Docker
1. Install Docker, copy the project up, create `.env`.
2. `docker compose up -d --build`. The frontend container serves the site on :8080 and proxies `/api` to the backend, so no CORS setup is needed.
3. Put HTTPS in front with Caddy (automatic certificates):
```
# /etc/caddy/Caddyfile
register.yourdomain.com {
    reverse_proxy localhost:8080
}
```
4. Firewall: allow 22, 80, 443 only. Change `ports: ["8000:8000"]` to `["127.0.0.1:8000:8000"]` so the API isn't public.

## 5. Production: AWS
- **Simplest:** an EC2 instance (t3.small) and follow section 4. Use an Elastic IP and a security group opening 80/443/22 (22 from your IP only).
- **Managed containers:** build the two images, push to ECR, run the backend on App Runner or ECS Fargate (set the env vars from section 3, health check `/api/health`). Host the frontend build (`npm run build`, upload `dist/`) on S3 + CloudFront with a 403/404 to `/index.html` rule, built with `VITE_API_URL` set to the API's HTTPS URL, and set `CORS_ORIGINS` to the CloudFront domain.
- **Database:** keep Supabase, or use RDS Postgres and just change `DATABASE_URL`. (The RLS step is skipped-safe on RDS; it simply isn't needed.)

## 6. Before real use
- Use a long random `SECRET_KEY` and change the seeded admin password.
- Turn on Supabase daily backups. Audit records and body records are legal evidence.
- Add Alembic migrations before changing the schema in production (`create_all` only creates missing tables).
- Scanning: implement `backend/app/ocr.py` (`extract_fields`). The UI already treats results as a draft staff must verify.
- Rate-limit `/api/auth/login` (e.g. at Caddy/Cloudflare) to slow password guessing.
