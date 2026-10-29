from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from .config import CORS_ORIGINS, ADMIN_USERNAME, ADMIN_PASSWORD
from .db import Base, engine, SessionLocal
from . import models
from .models import User, Service
from .security import hash_pw
from .routers import auth, users, bodies, services

def harden():
    """Postgres only. Why: (1) RLS with no policies blocks Supabase's public REST API from
    reading these tables; our backend connects as the owner role and is unaffected.
    (2) The trigger makes audit_log append-only even if app code or a DBA slips."""
    with engine.begin() as c:
        for t in Base.metadata.tables:
            c.execute(text(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY'))
        c.execute(text("CREATE OR REPLACE FUNCTION audit_immutable() RETURNS trigger AS $$ "
                       "BEGIN RAISE EXCEPTION 'audit_log is append-only'; END; $$ LANGUAGE plpgsql"))
        c.execute(text("DROP TRIGGER IF EXISTS audit_no_change ON audit_log"))
        c.execute(text("CREATE TRIGGER audit_no_change BEFORE UPDATE OR DELETE ON audit_log "
                       "FOR EACH ROW EXECUTE FUNCTION audit_immutable()"))

def seed(db):
    if not db.scalar(select(User).limit(1)):
        db.add(User(username=ADMIN_USERNAME, full_name="Administrator", role="admin",
                    password_hash=hash_pw(ADMIN_PASSWORD), must_change_password=True))
    if not db.scalar(select(Service).limit(1)):
        db.add_all([Service(name="Washing", price=10000), Service(name="Embalming", price=60000),
                    Service(name="Clothing", price=15000)])
    db.commit()

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        harden()
    with SessionLocal() as db:
        seed(db)
    yield

app = FastAPI(title="Mortuary register", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
for m in (auth, users, bodies, services):
    app.include_router(m.r)

@app.get("/api/health")
def health():
    return {"ok": True}
