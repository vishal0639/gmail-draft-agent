from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_user_id
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.draft import (
    DraftGenerateRequest,
    DraftListResponse,
    DraftOut,
    DraftUpdateRequest,
)
from app.services import draft_service

router = APIRouter()


def _to_out(d) -> DraftOut:  # noqa: ANN001
    return DraftOut(
        id=d.id,
        user_id=d.user_id,
        thread_id=d.thread_id,
        source_message_id=d.source_message_id,
        subject=d.subject,
        body=d.body,
        tone=d.tone,
        status=d.status,
        gmail_draft_id=d.gmail_draft_id,
        error_message=d.error_message,
        created_at=d.created_at,
        updated_at=d.updated_at,
        expires_at=d.expires_at,
    )


@router.post("/generate", response_model=DraftOut)
def generate_draft(
    body: DraftGenerateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> DraftOut:
    try:
        d = draft_service.generate_draft(db, user_id, body)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_out(d)


@router.get("", response_model=DraftListResponse)
def list_drafts(
    user_id: str = Depends(get_user_id),
    status: str | None = Query(default=None, description="Filter e.g. pending_review"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> DraftListResponse:
    items, total = draft_service.list_drafts(db, user_id, status=status, limit=limit)
    return DraftListResponse(items=[_to_out(d) for d in items], total=total)


@router.get("/{draft_id}", response_model=DraftOut)
def get_draft(
    draft_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> DraftOut:
    d = draft_service.get_draft(db, user_id, draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="Draft not found")
    return _to_out(d)


@router.patch("/{draft_id}", response_model=DraftOut)
def edit_draft(
    draft_id: str,
    body: DraftUpdateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> DraftOut:
    try:
        d = draft_service.update_draft_body(
            db, user_id, draft_id, body.body, body.subject
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_out(d)


@router.post("/{draft_id}/approve", response_model=DraftOut)
def approve_draft(
    draft_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> DraftOut:
    try:
        d = draft_service.approve_draft(db, user_id, draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_out(d)


@router.post("/{draft_id}/reject", response_model=DraftOut)
def reject_draft(
    draft_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> DraftOut:
    try:
        d = draft_service.reject_draft(db, user_id, draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_out(d)


@router.delete("/{draft_id}", response_model=MessageResponse)
def delete_draft(
    draft_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        draft_service.delete_draft(db, user_id, draft_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return MessageResponse(message="Draft removed")
