import json
import logging
from html import escape
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_user_id
from app.db.session import get_db
from app.schemas.auth import GoogleAuthUrlResponse
from app.schemas.common import MessageResponse
from app.services import auth_service, gmail_data

_log = logging.getLogger(__name__)
router = APIRouter()

OAUTH_POSTMESSAGE_TYPE = "gmail-agent-oauth"


def _frontend_origin(frontend_base: str) -> str:
    p = urlparse(frontend_base)
    if not p.scheme or not p.netloc:
        return "*"
    return f"{p.scheme}://{p.netloc}"


def _oauth_success_browser_html(frontend: str, user_id: str, email: str) -> str:
    fe = frontend.rstrip("/")
    origin = _frontend_origin(fe)
    payload = {
        "type": OAUTH_POSTMESSAGE_TYPE,
        "ok": True,
        "userId": user_id,
        "email": email or "",
    }
    payload_json = json.dumps(payload)
    origin_json = json.dumps(origin)
    done_url = f"{fe}/oauth-done"
    fb_qs = urlencode({"oauth": "1", "user_id": user_id, "email": email or ""})
    fallback_url = f"{fe}/?{fb_qs}"
    done_js = json.dumps(done_url)
    fallback_js = json.dumps(fallback_url)
    done_href = escape(done_url, quote=True)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Signing in</title></head><body>
<script>
(function() {{
  var payload = {payload_json};
  var origin = {origin_json};
  try {{
    if (window.opener && !window.opener.closed) {{
      window.opener.postMessage(payload, origin);
      window.location.replace({done_js});
    }} else {{
      window.location.replace({fallback_js});
    }}
  }} catch (e) {{
    window.location.replace({fallback_js});
  }}
}})();
</script>
<p style="font-family:sans-serif">Finishing sign-in… <a href="{done_href}">Continue</a></p>
</body></html>"""


def _oauth_error_browser_html(
    frontend: str,
    error_code: str,
    error_description: str | None,
) -> str:
    fe = frontend.rstrip("/")
    origin = _frontend_origin(fe)
    payload = {
        "type": OAUTH_POSTMESSAGE_TYPE,
        "ok": False,
        "reason": error_code,
        "detail": (error_description or "")[:500],
    }
    payload_json = json.dumps(payload)
    origin_json = json.dumps(origin)
    cancel_url = f"{fe}/oauth-cancel"
    cancel_js = json.dumps(cancel_url)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sign-in</title></head><body>
<script>
(function() {{
  var payload = {payload_json};
  var origin = {origin_json};
  try {{
    if (window.opener && !window.opener.closed) {{
      window.opener.postMessage(payload, origin);
    }}
  }} catch (e) {{}}
  window.location.replace({cancel_js});
}})();
</script>
<p style="font-family:sans-serif"><a href="{escape(cancel_url, quote=True)}">Continue</a></p>
</body></html>"""


@router.get("/gmail/health")
def gmail_token_health(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Verify we can read Gmail (good for expired/invalid token debugging)."""
    try:
        creds = auth_service.credentials_for_user(db, user_id)
        service = gmail_data.get_gmail_service(creds)
        u = gmail_data.get_user_profile(service)
        return {"ok": True, "emailAddress": u.get("emailAddress")}
    except Exception as e:  # noqa: BLE001
        _log.warning("Gmail health failed: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "hint": "Re-run OAuth2 with prompt=consent if the refresh token is invalid or revoked",
        }


@router.get("/google", response_model=GoogleAuthUrlResponse)
def start_google_oauth(db: Session = Depends(get_db)) -> GoogleAuthUrlResponse:
    """Start OAuth2: return URL to open in a browser. Stores CSRF `state` server-side."""
    st = auth_service.create_oauth_state(db)
    url = auth_service.get_authorization_url_with_state(st)
    return GoogleAuthUrlResponse(url=url, state=st)


@router.get("/google/callback", response_model=None)
def google_callback(
    _request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    oauth_format: str | None = Query(None, alias="format"),
    db: Session = Depends(get_db),
) -> HTMLResponse | JSONResponse:
    s = get_settings()
    fe = (s.frontend_oauth_success_url or "http://localhost:3000").rstrip("/")
    want_json = (oauth_format or "").lower() == "json"

    if error:
        if want_json:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": error,
                    "error_description": error_description,
                },
            )
        return HTMLResponse(
            content=_oauth_error_browser_html(fe, error, error_description),
            status_code=200,
        )

    if not code or not state:
        if want_json:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Missing code or state query parameters"},
            )
        return HTMLResponse(
            content=_oauth_error_browser_html(fe, "invalid_request", "Missing code or state"),
            status_code=200,
        )
    try:
        user = auth_service.exchange_code_and_upsert_user(db, code=code, state=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        _log.exception("OAuth callback failed")
        hint = str(e).strip() or type(e).__name__
        raise HTTPException(
            status_code=500,
            detail=f"OAuth token exchange failed: {hint}",
        ) from e

    if want_json:
        return JSONResponse(
            content={
                "ok": True,
                "user_id": user.id,
                "email": user.email or "",
            }
        )

    # Browser: postMessage to opener (no user_id in address bar), then /oauth-done; no opener → URL fallback.
    return HTMLResponse(content=_oauth_success_browser_html(fe, user.id, user.email or ""))


@router.post("/revoke", response_model=MessageResponse)
def revoke_google(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Logout: revoke access with Google and remove local tokens."""
    try:
        auth_service.revoke_and_clear_local(db, user_id)
    except Exception as e:  # noqa: BLE001
        _log.warning("Revoke had issues: %s", e)
    return MessageResponse(message="Local session cleared; re-auth if needed")
