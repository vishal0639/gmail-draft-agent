/**
 * Client for the Draftly Python backend (FastAPI /api/v1).
 */

const LS_API = "gmailagent_api_base";
const LS_API_LEGACY = "draftly_api_base";

function readApiBaseFromStorage(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LS_API) || localStorage.getItem(LS_API_LEGACY);
}

/**
 * In the browser, default to same-origin `/api/v1` so Next can proxy to FastAPI (see `next.config.ts` rewrites).
 * Override with `NEXT_PUBLIC_API_BASE_URL` or saved Settings / localStorage when you call the API directly.
 */
export function getApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    const o = readApiBaseFromStorage();
    if (o?.trim()) return o.trim().replace(/\/$/, "");
    return "/api/v1";
  }
  // Server / scripts: no proxy; use loopback
  return "http://127.0.0.1:8000/api/v1";
}

/** Prefer Redux/session override (in-memory) when set; else localStorage + default. */
export function resolveApiBase(override?: string | null): string {
  const t = override?.trim();
  if (t) return t.replace(/\/$/, "");
  return getApiBase();
}

function backendDownMessage(): string {
  return [
    "The API backend is not reachable.",
    "In one terminal: cd backend then run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000",
    "Keep the Next app running (npm run dev). The UI calls /api/… on this port and Next proxies to port 8000.",
  ].join(" ");
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestInit & { userId?: string | null; apiBase?: string | null } = {},
): Promise<T> {
  const { userId, apiBase, headers: h, ...rest } = options;
  const base = resolveApiBase(apiBase);
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(h);
  if (!headers.has("Content-Type") && rest.body && typeof rest.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  if (userId) {
    headers.set("X-User-Id", userId);
  }
  let res: Response;
  try {
    res = await fetch(url, { ...rest, headers });
  } catch (e) {
    const isNetwork =
      e instanceof TypeError && (e.message === "Failed to fetch" || e.message.includes("Load failed"));
    if (isNetwork) {
      throw new Error(
        base.startsWith("http")
          ? `${backendDownMessage()} (Tried: ${base})`
          : `${backendDownMessage()} (Tried: ${base} via this app)`,
      );
    }
    throw e;
  }
  const text = await res.text();
  const data = text ? (() => { try { return JSON.parse(text); } catch { return text; } })() : null;
  if (res.status === 502 || res.status === 503 || res.status === 504) {
    throw new Error(
      `Bad gateway / upstream error (${res.status}). ${backendDownMessage()}`,
    );
  }
  if (!res.ok) {
    const msg =
      typeof data === "object" && data && "detail" in (data as object)
        ? String((data as { detail: unknown }).detail)
        : res.statusText;
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return data as T;
}
