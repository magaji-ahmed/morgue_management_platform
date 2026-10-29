from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from ..audit import log
from ..db import get_db
from ..models import User
from ..schemas import UserIn, UserPatch, user_out
from ..security import admin_only, hash_pw

r = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(admin_only)])

@r.get("")
def list_users(db=Depends(get_db)):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.id))]

@r.post("")
def create_user(d: UserIn, admin=Depends(admin_only), db=Depends(get_db)):
    name = d.username.strip().lower()
    if db.scalar(select(User).where(User.username == name)):
        raise HTTPException(400, "That username is taken.")
    if d.role not in ("admin", "staff"):
        raise HTTPException(400, "Role must be admin or staff.")
    u = User(username=name, full_name=d.full_name, password_hash=hash_pw(d.password), role=d.role)
    db.add(u)
    log(db, admin, "created account", detail=f"{name} ({d.role})")
    db.commit()
    return user_out(u)

@r.patch("/{uid}")
def update_user(uid: int, d: UserPatch, admin=Depends(admin_only), db=Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.status == "deleted":
        raise HTTPException(404, "Account not found.")
    if u.id == admin.id and (d.status or d.role):
        raise HTTPException(400, "You can't suspend or demote your own account.")
    if d.status and d.status not in ("active", "suspended"):
        raise HTTPException(400, "Status must be active or suspended.")
    if d.role and d.role not in ("admin", "staff"):
        raise HTTPException(400, "Role must be admin or staff.")
    changes = []
    for k in ("full_name", "role", "status"):
        v = getattr(d, k)
        if v and v != getattr(u, k):
            changes.append(f"{k}: {getattr(u, k)} -> {v}")
            setattr(u, k, v)
    if d.password:
        u.password_hash, u.must_change_password = hash_pw(d.password), True
        changes.append("password reset")
    log(db, admin, "updated account", detail=f"{u.username}: " + "; ".join(changes))
    db.commit()
    return user_out(u)

@r.delete("/{uid}")
def delete_user(uid: int, admin=Depends(admin_only), db=Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.status == "deleted":
        raise HTTPException(404, "Account not found.")
    if u.id == admin.id:
        raise HTTPException(400, "You can't delete your own account.")
    u.status = "deleted"  # soft delete: audit rows still point at this person
    log(db, admin, "deleted account", detail=u.username)
    db.commit()
    return {"ok": True}
