import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_user_id
from app.db.session import get_db
from app.schemas.email import EmailDetailResponse, EmailListResponse, EmailItem
from app.services import auth_service, gmail_data

_log = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=EmailListResponse)
def list_emails(
    user_id: str = Depends(get_user_id),
    filter: str = Query("unread", description="unread | recent | all"),
    max_results: int = Query(20, ge=1, le=100),
    page_token: str | None = Query(
        None,
        description="Gmail list nextPageToken from a previous response for pagination",
    ),
    db: Session = Depends(get_db),
) -> EmailListResponse:
    try:
        creds = auth_service.credentials_for_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    service = gmail_data.get_gmail_service(creds)
    try:
        items, est, next_tok = gmail_data.list_messages(
            service,
            filter_kind=filter,
            max_results=max_results,
            page_token=page_token,
        )
    except Exception as e:  # noqa: BLE001
        _log.exception("List messages")
        raise HTTPException(status_code=502, detail=f"Gmail API error: {e}") from e
    return EmailListResponse(
        items=[EmailItem(**x) for x in items],
        result_size_estimate=est,
        next_page_token=next_tok,
    )


@router.get("/{message_id}", response_model=EmailDetailResponse)
def get_email(
    message_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> EmailDetailResponse:
    try:
        creds = auth_service.credentials_for_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    service = gmail_data.get_gmail_service(creds)
    try:
        p = gmail_data.get_message_full(service, message_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Message not found: {e}") from e
    return EmailDetailResponse(
        id=p.get("id") or message_id,
        thread_id=p.get("thread_id"),
        subject=p.get("subject"),
        from_addr=p.get("from_addr"),
        snippet=p.get("snippet"),
        internal_date=p.get("internal_date"),
        label_ids=p.get("label_ids") or [],
        body_text=p.get("body_text"),
        body_html=p.get("body_html"),
        message_id_rfc=p.get("message_id_rfc"),
        in_reply_to=p.get("in_reply_to"),
        references=p.get("references"),
        to_addresses=p.get("to_addresses"),
    )
