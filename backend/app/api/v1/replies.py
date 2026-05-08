import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.deps import get_user_id
from app.db.session import get_db
from app.schemas.reply import SendReplyRequest
from app.services import send_service

router = APIRouter()


@router.post("/send")
def send_reply(
    body: SendReplyRequest,
    user_id: str = Depends(get_user_id),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", description="UUID recommended"
    ),
    db: Session = Depends(get_db),
) -> dict:
    key = idempotency_key or str(uuid.uuid4())
    if len(key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key too long")
    try:
        return send_service.send_approved_draft(
            db, user_id, body.draft_id, idempotency_key=key
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(e) or "Send failed") from e
