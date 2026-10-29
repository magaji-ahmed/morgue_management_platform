from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from ..audit import log
from ..db import get_db
from ..models import User
from ..schemas import LoginIn, PasswordIn, user_out
from ..security import check_pw, hash_pw, make_token, current_user

r = APIRouter(prefix="/api/auth", tags=["auth"])

@r.post("/login")
def login(d: LoginIn, db=Depends(get_db)):
    u = db.scalar(select(User).where(User.username == d.username.strip().lower()))
    if not u or u.status == "deleted" or not check_pw(d.password, u.password_hash):
        raise HTTPException(401, "Wrong username or password.")
    if u.status != "active":
        raise HTTPException(403, "This account is suspended. Contact an admin.")
    log(db, u, "signed in")
    db.commit()
    return {"token": make_token(u.id), "user": user_out(u)}

@r.get("/me")
def me(u=Depends(current_user)):
    return user_out(u)

@r.post("/change-password")
def change_password(d: PasswordIn, u=Depends(current_user), db=Depends(get_db)):
    if not check_pw(d.old_password, u.password_hash):
        raise HTTPException(400, "Current password is wrong.")
    u.password_hash, u.must_change_password = hash_pw(d.new_password), False
    log(db, u, "changed own password")
    db.commit()
    return {"token": make_token(u.id), "user": user_out(u)}
