from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_user_id
from app.db import models
from app.db.session import get_db

router = APIRouter()


@router.get("/audit")
def list_audit(
    user_id: str = Depends(get_user_id),
    event: str | None = Query(default=None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(models.AuditLog).filter_by(user_id=user_id)
    if event:
        q = q.filter_by(event=event)
    rows = q.order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "event": r.event,
                "details": r.details,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }
