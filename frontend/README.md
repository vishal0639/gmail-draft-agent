# GMailAgent — web UI

Next.js front end for the Gmail reply workflow: sign in, load mail, get suggested reply drafts, review, approve, send.

## Run

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

App: [http://localhost:3000](http://localhost:3000). Start the API (default `http://127.0.0.1:8000`) or set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` (and in-app Settings).

The browser stores your **account key** and optional **API base** under `gmailagent_*` keys; older `draftly_*` values are still read for migration.

## Internal Server Error (500) on `localhost:3000`

That is almost always a **broken `.next` cache** (e.g. cache deleted while `next dev` was still running, or a failed write). Do this:

1. **Stop** the dev server (Ctrl+C in the terminal that runs `npm run dev`).
2. Delete the cache folder: remove `frontend/.next` (Explorer or `Remove-Item -Recurse -Force .next` in PowerShell from the `frontend` directory).
3. Start again: `npm run dev`

Or in one go from `frontend`: `npm run dev:clean` (deletes `.next` then starts the dev server).
