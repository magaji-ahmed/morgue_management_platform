import math
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, or_
from ..audit import log
from ..config import DAILY_RATE
from ..db import get_db
from ..models import AuditLog, Body, BodyService, Payment, Service, now
from ..ocr import extract_fields
from ..schemas import ApplyService, BodyCreate, BodyIn, PaymentIn, DoneIn
from ..security import staff

r = APIRouter(prefix="/api/bodies", tags=["bodies"], dependencies=[Depends(staff)])
FIELDS = list(BodyIn.model_fields)


def open_check(b):
    if b.status == "released":
        raise HTTPException(400, "This body has already been released.")


def get_line(b, lid):
    line = next((x for x in b.services if x.id == lid), None)
    if not line:
        raise HTTPException(404, "That service isn't on this body's list.")
    return line


def select_service(db, b, sid, u):
    s = db.get(Service, sid)
    if not s or not s.active:
        raise HTTPException(404, "That service isn't available.")
    if any(x.service_id == sid for x in b.services):
        raise HTTPException(400, f"{s.name} is already on this list.")
    b.services.append(
        BodyService(service_id=s.id, name=s.name, price=s.price, added_by=u.username)
    )
    log(db, u, "service added to list", b.id, f"{s.name} @ {s.price:.2f}")


def receipt(b):
    end = b.released_at or now()
    days = max(
        1, math.ceil((end - b.admitted_at).total_seconds() / 86400)
    )  # part of a day counts as a full day
    storage = days * DAILY_RATE
    services = sum(s.price for s in b.services)
    paid = sum(p.amount for p in b.payments)
    return {
        "days": days,
        "daily_rate": DAILY_RATE,
        "storage": storage,
        "services": services,
        "total": storage + services,
        "paid": paid,
        "balance": storage + services - paid,
    }


def out(b, full=False):
    d = {
        "id": b.id,
        "tag_no": b.tag_no,
        "status": b.status,
        "admitted_at": b.admitted_at,
        "released_at": b.released_at,
        "contact_missing": not (b.contact_name and b.contact_phone),
        **{f: getattr(b, f) for f in FIELDS},
    }
    if full:
        d["services"] = [
            {
                "id": s.id,
                "service_id": s.service_id,
                "name": s.name,
                "price": s.price,
                "done": s.done,
                "done_by": s.done_by,
                "done_at": s.done_at,
                "added_by": s.added_by,
            }
            for s in b.services
        ]
        d["payments"] = [
            {
                "id": p.id,
                "amount": p.amount,
                "note": p.note,
                "received_by": p.received_by,
                "paid_at": p.paid_at,
            }
            for p in b.payments
        ]
        d["receipt"] = receipt(b)
    return d


def get_body(db, bid):
    b = db.get(Body, bid)
    if not b:
        raise HTTPException(404, "Body record not found.")
    return b


@r.get("")
def list_bodies(q: str = "", db=Depends(get_db)):
    s = select(Body).order_by(Body.id.desc()).limit(200)
    if q:
        like = f"%{q}%"
        s = s.where(
            or_(
                Body.full_name.ilike(like),
                Body.tag_no.ilike(like),
                Body.contact_name.ilike(like),
            )
        )
    return [out(b) for b in db.scalars(s)]


@r.post("/scan")
async def scan(file: UploadFile, u=Depends(staff), db=Depends(get_db)):
    draft = extract_fields(await file.read(), file.content_type)
    log(db, u, "scanned paper form", detail=file.filename)
    db.commit()
    return {"draft": draft}


@r.post("")
def register(d: BodyCreate, u=Depends(staff), db=Depends(get_db)):
    b = Body(**d.model_dump(exclude={"service_ids"}), registered_by=u.id)
    db.add(b)
    db.flush()
    b.tag_no = f"MB-{b.admitted_at.year}-{b.id:05d}"
    log(db, u, "registered body", b.id, b.full_name or "unidentified")
    for sid in dict.fromkeys(
        d.service_ids
    ):  # dict.fromkeys drops duplicate ids, keeps order
        select_service(db, b, sid, u)
    db.commit()
    return out(b, True)


@r.get("/{bid}")
def detail(bid: int, db=Depends(get_db)):
    return out(get_body(db, bid), True)


@r.patch("/{bid}")
def edit(bid: int, d: BodyIn, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    changes = []
    for k, v in d.model_dump().items():
        if getattr(b, k) != v:
            changes.append(f"{k}: {getattr(b, k)!r} -> {v!r}")
            setattr(b, k, v)
    if changes:
        log(db, u, "edited details", b.id, "; ".join(changes))
    db.commit()
    return out(b, True)


@r.post("/{bid}/services")
def add_service(bid: int, d: ApplyService, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    open_check(b)
    select_service(db, b, d.service_id, u)
    db.commit()
    return out(b, True)


@r.delete("/{bid}/services/{lid}")
def remove_service(bid: int, lid: int, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    open_check(b)
    line = get_line(b, lid)
    if line.done:
        raise HTTPException(400, "Mark it undone before removing it.")
    log(db, u, "service removed from list", b.id, line.name)
    db.delete(line)
    db.commit()
    return out(b, True)


@r.post("/{bid}/services/{lid}/done")
def mark_done(bid: int, lid: int, d: DoneIn, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    open_check(b)
    line = get_line(b, lid)
    if line.done == d.done:
        raise HTTPException(400, "It's already marked that way.")
    line.done = d.done
    line.done_by, line.done_at = (u.username, now()) if d.done else (None, None)
    log(
        db,
        u,
        "service marked done" if d.done else "service marked undone",
        b.id,
        line.name,
    )
    db.commit()
    return out(b, True)


@r.post("/{bid}/payments")
def pay(bid: int, d: PaymentIn, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    b.payments.append(Payment(amount=d.amount, note=d.note, received_by=u.username))
    log(db, u, "payment received", b.id, f"{d.amount:.2f} {d.note or ''}".strip())
    db.commit()
    return out(b, True)


@r.post("/{bid}/release")
def release(bid: int, u=Depends(staff), db=Depends(get_db)):
    b = get_body(db, bid)
    if b.status == "released":
        raise HTTPException(400, "Already released.")
    if not (b.contact_name and b.contact_phone):
        raise HTTPException(
            400, "Add a contact person (name and phone) before release."
        )
    if receipt(b)["balance"] > 0:
        raise HTTPException(400, "Outstanding balance. Record payment before release.")
    b.status, b.released_at = "released", now()
    log(db, u, "released body", b.id, f"to {b.contact_name}")
    db.commit()
    return out(b, True)


@r.get("/{bid}/audit")
def audit(bid: int, db=Depends(get_db)):
    rows = db.scalars(
        select(AuditLog).where(AuditLog.body_id == bid).order_by(AuditLog.id.desc())
    )
    return [
        {"at": a.at, "username": a.username, "action": a.action, "detail": a.detail}
        for a in rows
    ]
