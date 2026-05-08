from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_user_id
from app.db.session import get_db
from app.schemas.preferences import UserPreferencesIn, UserPreferencesOut
from app.services import preferences_service

router = APIRouter()


@router.get("", response_model=UserPreferencesOut)
def get_preferences(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> UserPreferencesOut:
    try:
        p = preferences_service.get_prefs_dict(db, user_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return UserPreferencesOut(
        default_tone=p.get("default_tone", "concise"),
        email_signature=p.get("email_signature", ""),
        other=p.get("other") if p.get("other") else None,
    )


@router.put("", response_model=UserPreferencesOut)
def put_preferences(
    body: UserPreferencesIn,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> UserPreferencesOut:
    try:
        p = preferences_service.upsert_preferences(
            db,
            user_id,
            {
                "default_tone": body.default_tone,
                "email_signature": body.email_signature,
                "other": body.other,
            },
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return UserPreferencesOut(
        default_tone=p.get("default_tone", "concise"),
        email_signature=p.get("email_signature", ""),
        other=p.get("other") if p.get("other") else None,
    )
