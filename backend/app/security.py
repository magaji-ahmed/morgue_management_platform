from datetime import datetime, timedelta, timezone
import bcrypt, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from .config import SECRET_KEY, TOKEN_HOURS
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)

def hash_pw(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_pw(p, h): return bcrypt.checkpw(p.encode(), h.encode())

def make_token(uid):
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": str(uid), "exp": exp}, SECRET_KEY, algorithm="HS256")

def current_user(creds=Depends(bearer), db=Depends(get_db)):
    if not creds:
        raise HTTPException(401, "Sign in to continue.")
    try:
        uid = int(jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Your session expired. Sign in again.")
    u = db.get(User, uid)  # re-checked on every request so suspending an account takes effect immediately
    if not u or u.status != "active":
        raise HTTPException(401, "This account is not active.")
    return u

def staff(u=Depends(current_user)):
    if u.must_change_password:
        raise HTTPException(403, "Change your password before continuing.")
    return u

def admin_only(u=Depends(staff)):
    if u.role != "admin":
        raise HTTPException(403, "Only admins can do this.")
    return u
