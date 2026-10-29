from .models import AuditLog

def log(db, user, action, body_id=None, detail=None):
    """Adds to the caller's session so the log row commits atomically with the action itself."""
    db.add(AuditLog(user_id=user.id, username=user.username, body_id=body_id, action=action, detail=detail))
