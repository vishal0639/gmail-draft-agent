"""
MVP: identify the user via `X-User-Id` header (UUID from OAuth callback response).
Replace with JWT / session cookies for production.
"""

from fastapi import Header, HTTPException

REQUIRED = "Set X-User-Id to the user id returned by OAuth (see README)."


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id or not str(x_user_id).strip():
        raise HTTPException(status_code=401, detail=REQUIRED)
    return str(x_user_id).strip()
