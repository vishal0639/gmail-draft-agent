# GMailAgent — web UI

Next.js front end for the Gmail reply workflow: sign in, load mail, get suggested reply drafts, review, approve, send.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000).

**Backend:** start the API (see `../backend/README.md`), default [http://127.0.0.1:8000](http://127.0.0.1:8000).  
Next.js **rewrites** `/api/*` → `${BACKEND_URL}/api/*` (`BACKEND_URL` defaults to `http://127.0.0.1:8000`). The browser usually calls **`/api/v1/...`** on the same origin, so **no `.env` file is required** for local dev.

### Optional overrides

- **`NEXT_PUBLIC_API_BASE_URL`** — direct API base (e.g. `http://127.0.0.1:8000/api/v1`). Also respected when set at build time for the client bundle.
- **`BACKEND_URL`** — where rewrites should proxy during **`next build`** / **`next start`** (set this on your host if the API is not at `127.0.0.1:8000`).

Copy `.env.local.example` to `.env.local` only if you need those overrides.

The browser stores your **account key** and optional **API base** under `gmailagent_*` keys in localStorage; older `draftly_*` keys are still read for migration.

## Production build

```bash
npm run build
npm start
```

Set **`BACKEND_URL`** in the environment when building/running if the FastAPI server URL differs from the default (e.g. deployed API URL).

## Internal Server Error (500) on `localhost:3000`

That is almost always a **broken `.next` cache** (e.g. cache deleted while `next dev` was still running, or a failed write). Do this:

1. **Stop** the dev server (Ctrl+C in the terminal that runs `npm run dev`).
2. Delete the cache folder: remove `frontend/.next` (Explorer or `Remove-Item -Recurse -Force .next` in PowerShell from the `frontend` directory).
3. Start again: `npm run dev`

Or from `frontend`: **`npm run dev:clean`** (deletes `.next` then starts the dev server).

## `'next' is not recognized` / missing `react`

Run **`npm install`** from `frontend` so `node_modules/.bin` and packages like `react` are present.
