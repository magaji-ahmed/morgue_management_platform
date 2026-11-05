from fastapi import APIRouter, Depends
from ..audit import log
from ..config import DAILY_RATE
from ..db import get_db
from ..models import Setting
from ..schemas import RatesIn
from ..security import staff, admin_only

r = APIRouter(prefix="/api/settings", tags=["settings"])


def get_rate(db, origin):
    s = db.get(Setting, f"rate_{origin}")
    return s.value if s else DAILY_RATE


@r.get("/rates")
def rates(db=Depends(get_db), u=Depends(staff)):
    return {k: get_rate(db, k) for k in ("internal", "external")}


@r.put("/rates")
def set_rates(d: RatesIn, admin=Depends(admin_only), db=Depends(get_db)):
    old = {k: get_rate(db, k) for k in ("internal", "external")}
    for k, v in d.model_dump().items():
        s = db.get(Setting, f"rate_{k}")
        if s:
            s.value = v
        else:
            db.add(Setting(key=f"rate_{k}", value=v))
    log(
        db,
        admin,
        "changed daily rates",
        detail=f"internal {old['internal']:.2f} -> {d.internal:.2f}; external {old['external']:.2f} -> {d.external:.2f}",
    )
    db.commit()
    return {"internal": d.internal, "external": d.external}
