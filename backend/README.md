# Draftly (Gmail AI Reply Agent) — Backend

Python (FastAPI) backend for the **Airtribe / Draftly** case study: **OAuth2** to Google, **Gmail** read (unread/recent) and **send** (only after **approval**), **OpenAI-powered** reply drafts when `OPENAI_API_KEY` is set (otherwise a **mock** draft for local dev), **encrypted** tokens and **preferences** at rest, **idempotent** sends with **retries** on transient Gmail errors, and **audit** logging.

> Scope matches the case-study brief: connect Gmail, list messages, create/manage drafts, human-in-the-loop, send with threading, logs, and failure handling. The files `gmail.txt` / `gmail-summary.txt` in the repo describe a different (QA) concept—this backend implements the **Gmail** brief only.

---

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env
```

#### Database: PostgreSQL, MySQL, or SQLite

Set **`DATABASE_URL`** in `.env`. `pip install -r requirements.txt` installs **psycopg** (PostgreSQL) and **PyMySQL** (MySQL).

**PostgreSQL** (e.g. **Neon**, Supabase, RDS, local):

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

The app maps bare `postgresql://` (and `postgres://`) to **`postgresql+psycopg://`** so SQLAlchemy uses **psycopg** v3. For Neon, paste the connection string from the dashboard (keep `sslmode=require`).

Start the API once; tables are created from models (`init_db`) unless you use Alembic.

**MySQL** — use a URL like:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/draftly?charset=utf8mb4
```

Create the database and user in MySQL, then start the API.

**SQLite** — `DATABASE_URL=sqlite:///./draftly.db` (zero-config). SQLite **does** persist across app restarts; it only “resets” if the `.db` file is removed, you change `DATABASE_URL`, or a script recreates the DB.

**Google OAuth and encryption**

1. In **Google Cloud Console** create a project, enable the **Gmail API**, and create **OAuth 2.0** credentials of type **Web application**.
2. Add an **authorized redirect URI** (must match `GOOGLE_REDIRECT_URI` in `.env` exactly), e.g. `http://127.0.0.1:8000/api/v1/auth/google/callback`.
3. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `.env`.
4. Generate a **Fernet** key and set `MASTER_ENCRYPTION_KEY`:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

5. **Draft generation (OpenAI):** set `OPENAI_API_KEY` in `.env` for real LLM replies using thread context and optional style hints from recent **Sent** mail. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`). If the key is empty, the server still works using the built-in mock draft text.

### Run the server

From the `backend/` directory (with `.env` configured and dependencies installed):

**Windows — short scripts**

```powershell
.\run.ps1
```

Or double-click / run: `run.cmd`

These call Uvicorn on `127.0.0.1:8000` and create `.venv` + install `requirements.txt` if needed.

**Manual (any OS)**

Activate the venv, then:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Windows without activating the venv**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use `--host 0.0.0.0` instead of `127.0.0.1` if you need other machines on the LAN to reach the API.

To simply run backend use below command:-
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

- API root: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>

### First-time OAuth (MVP)

1. `GET /api/v1/auth/google` → open `url` in a browser, complete Google consent.
2. The callback redirects to **`FRONTEND_OAUTH_SUCCESS_URL`** (default `http://localhost:3000`) with **`?oauth=1&user_id=...&email=...`**; the web UI saves the account key and clears the query string. For API clients (curl/Postman), send header **`X-User-Id: <uuid>`** on each request.
3. Optional: `GET /api/v1/auth/gmail/health` with `X-User-Id` to confirm Gmail access.

If you open the UI at **`http://127.0.0.1:3000`** but `FRONTEND_OAUTH_SUCCESS_URL` is **`http://localhost:3000`**, set **`FRONTEND_OAUTH_SUCCESS_URL`** in `.env` to match the origin you use (or you may appear “not logged in” until you refresh from the same host).

> **Production** should use cookies or JWT instead of a raw `X-User-Id` header; the header is a deliberate simplification for the capstone and Postman use.

### Google OAuth: “Access blocked” / `403 access_denied`

While the OAuth consent screen is in **Testing**, Google only allows sign-in for accounts listed under **Test users**. Everyone else sees “has not completed verification” / access denied.

**Fix (no code change):**

1. Open [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **OAuth consent screen**.
2. In **Test users**, click **Add users** and add each Google account that should be able to sign in (for example the account you use in the browser).
3. Save, wait a short moment, then try **Start Google sign-in** again.

Publishing the app for “any Google user” usually requires **Google’s verification** for sensitive scopes (Gmail); for local development, **Testing + test users** is normal.

### `OAuth token exchange failed` after you approve Google

Usually fixed in code by **not using PKCE** across two separate `Flow` instances (authorization vs callback). This backend uses the **web client + client secret** flow without PKCE so the callback can exchange the code. If you still see errors, check **`GOOGLE_REDIRECT_URI`** matches the console exactly, **`MASTER_ENCRYPTION_KEY`** is set, and watch the uvicorn log for the real exception.

---

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness |
| `GET` | `/api/v1/auth/google` | Get Google OAuth2 URL + `state` |
| `GET` | `/api/v1/auth/google/callback` | Browser redirect target (code exchange) |
| `POST` | `/api/v1/auth/revoke` | Revoke tokens + clear local (needs `X-User-Id`) |
| `GET` | `/api/v1/auth/gmail/health` | Gmail token sanity check |
| `GET` | `/api/v1/emails?filter=unread\|recent\|all&max_results=20` | List messages (metadata) |
| `GET` | `/api/v1/emails/{message_id}` | Message detail + body (best effort) |
| `POST` | `/api/v1/drafts/generate` | **Mock** draft (needs source Gmail `message_id`) |
| `GET` | `/api/v1/drafts` | List drafts; optional `?status=` |
| `GET` | `/api/v1/drafts/{draft_id}` | Get one draft |
| `PATCH` | `/api/v1/drafts/{draft_id}` | Edit body (only `pending_review`) |
| `POST` | `/api/v1/drafts/{draft_id}/approve` | Approve (safety gate for send) |
| `POST` | `/api/v1/drafts/{draft_id}/reject` | Reject |
| `POST` | `/api/v1/replies/send` | Send **approved** draft; header `Idempotency-Key` |
| `GET` | `/api/v1/preferences` | Get preferences (defaults if missing) |
| `PUT` | `/api/v1/preferences` | Update (encrypted at rest) |
| `GET` | `/api/v1/logs/audit?event=&limit=` | Audit log |

**Draft status values:** `pending_review`, `approved`, `rejected`, `sent`, `failed`.

---

## HLD (high-level design)

```text
┌──────────────────┐     HTTPS / JSON      ┌─────────────────────┐
│  Client / Postman│ ◄───────────────────► │  FastAPI (REST)     │
└──────────────────┘                       └──────────┬──────────┘
                                                        │
            ┌──────────────────────┬────────────────────┼───────────────┐
            ▼                      ▼                    ▼               ▼
   ┌────────────────┐    ┌─────────────────┐   ┌────────────┐  ┌──────────┐
   │ Services       │    │ Google OAuth2   │   │ SQLite/    │  │ Security │
   │ (drafts, send, │    │ + Gmail API     │   │ (Postgres) │  │ (Fernet) │
   │  mock LLM)     │    │                 │   │            │  │          │
   └────────────────┘    └─────────────────┘   └────────────┘  └──────────┘
```

**Flows**

1. **Connect:** `auth` service exchanges code, stores **encrypted** refresh (and access cache), upserts `users`.
2. **Read mail:** `gmail_data` uses refreshed credentials, lists/loads messages, parser extracts bodies and RFC headers.
3. **Mock draft:** `mock_llm` + optional **preferences** (signature, default tone) → new `drafts` row in `pending_review`.
4. **Review:** user `PATCH` / `approve` / `reject` — only `approved` may send.
5. **Send:** `send_service` builds **RFC 822** reply, sets **In-Reply-To** / **References**, `messages.send` with `threadId`; **Idempotency-Key** + DB row avoid duplicate sends; **tenacity** retries 429/5xx.
6. **Observability:** `audit_logs` and send outcome stored for debugging and demos.

**Compliance with Gmail:** batch sizes are conservative on list; sending uses the official client library; respect your **quota** in Google Cloud; implement exponential backoff (partially via `tenacity` on send path).

---

## LLD (low-level design / modules)

| Path | Role |
|------|------|
| `app/main.py` | `FastAPI` app, CORS, lifespan, `init_db` |
| `app/core/config.py` | Pydantic settings from env |
| `app/core/deps.py` | `X-User-Id` → user scope (MVP) |
| `app/core/security.py` | Fernet **encrypt** / **decrypt** for tokens and JSON prefs |
| `app/db/models.py` | `User`, `OAuthState`, `GmailToken`, `UserPreferences`, `Draft`, `SendAttempt`, `AuditLog` |
| `app/db/session.py` | SQLAlchemy `engine`, `get_db` dependency, SQLite `PRAGMA foreign_keys` |
| `app/services/auth_service.py` | OAuth2 **Flow**, token **encryption**, `credentials_for_user` refresh, **revoke** |
| `app/services/gmail_data.py` | **Only file** with Gmail `users.*` API calls: `getProfile`, `messages.list`, `messages.get`, `messages.send` (see module docstring) |
| `app/services/gmail_parser.py` | MIME walk for plain/html + **Message-ID** / **In-Reply-To** |
| `app/services/mock_llm.py` | **Placeholder** string generator (replace with real LLM) |
| `app/services/draft_service.py` | Create/list/update draft lifecycle |
| `app/services/send_service.py` | MIME reply, `send` + **idempotency** + retries |
| `app/services/preferences_service.py` | **Encrypted** `user_preferences` blob |
| `app/api/v1/*` | Routers: `auth`, `emails`, `drafts`, `replies`, `preferences`, `logs`, `health` |
| `app/schemas/*` | Pydantic request/response DTOs |

**Idempotency:** `send_attempts` enforces `UNIQUE (user_id, idempotency_key)`. Same key → same response without a second Gmail send.

**Data at rest:** `GmailToken.enc_*` and `UserPreferences.enc_data` are **Fernet ciphertext**. Without `MASTER_ENCRYPTION_KEY`, the app will not start encrypt paths that require it; generate a key and keep it in a **secret store** in production.

---

## Design trade-offs (for your report)

- **Header `X-User-Id`:** simple for demos; replace with **OAuth session** or **JWT** for public deployments.
- **SQLite vs hosted SQL:** SQLite is zero-config (file `draftly.db`). For **PostgreSQL** or **MySQL**, set `DATABASE_URL` (see Quick start). Production should use **Alembic** migrations instead of only `create_all`.
- **Mock LLM:** isolates product logic from model vendors; add an interface `generate_reply(ctx) -> str` and swap the implementation.
- **CSRF `state`:** single-use store in `oauth_states`; in multi-instance production use **Redis** with TTL.

---

## License

As needed for your course / repository.
