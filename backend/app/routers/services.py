from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from ..audit import log
from ..db import get_db
from ..models import BodyService, Service
from ..schemas import ServiceIn
from ..security import staff, admin_only

r = APIRouter(prefix="/api/services", tags=["services"])


def taken(db, name, ignore_id=None):
    s = db.scalar(select(Service).where(Service.name == name))
    return s is not None and s.id != ignore_id


@r.get("")
def list_services(db=Depends(get_db), u=Depends(staff)):
    return [
        {"id": s.id, "name": s.name, "price": s.price, "active": s.active}
        for s in db.scalars(select(Service).order_by(Service.name))
    ]


@r.post("")
def add_service(d: ServiceIn, admin=Depends(admin_only), db=Depends(get_db)):
    d.name = d.name.strip()
    if taken(db, d.name):
        raise HTTPException(400, "A service with that name already exists.")
    s = Service(**d.model_dump())
    db.add(s)
    log(db, admin, "added service", detail=f"{d.name} @ {d.price:.2f}")
    db.commit()
    return {"id": s.id}


@r.patch("/{sid}")
def edit_service(sid: int, d: ServiceIn, admin=Depends(admin_only), db=Depends(get_db)):
    s = db.get(Service, sid)
    if not s:
        raise HTTPException(404, "Service not found.")
    d.name = d.name.strip()
    if taken(db, d.name, s.id):
        raise HTTPException(400, "A service with that name already exists.")
    log(
        db,
        admin,
        "edited service",
        detail=f"{s.name} {s.price:.2f} -> {d.name} {d.price:.2f}, active={d.active}",
    )
    s.name, s.price, s.active = d.name, d.price, d.active
    db.commit()
    return {"ok": True}


@r.delete("/{sid}")
def remove_service(sid: int, admin=Depends(admin_only), db=Depends(get_db)):
    s = db.get(Service, sid)
    if not s:
        raise HTTPException(404, "Service not found.")
    used = db.scalar(
        select(BodyService.id).where(BodyService.service_id == sid).limit(1)
    )
    log(
        db,
        admin,
        "removed service",
        detail=f"{s.name} ({'hidden, used on past records' if used else 'deleted'})",
    )
    if used:
        s.active = False  # hide it; deleting would break old receipts
    else:
        db.delete(s)
    db.commit()
    return {"ok": True}
