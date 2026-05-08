import { getApiBase } from "@/lib/api";

export const USER_KEY = "gmailagent_user_id";
export const USER_KEY_LEGACY = "draftly_user_id";
export const API_KEY = "gmailagent_api_base";
export const API_KEY_LEGACY = "draftly_api_base";

export function loadUserId(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY_LEGACY) || "";
}

export function loadApiBase(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(API_KEY) || localStorage.getItem(API_KEY_LEGACY) || getApiBase();
}

export function persistSession(userId: string, apiBase: string): void {
  const u = userId.trim();
  const a = apiBase.trim().replace(/\/$/, "");
  if (u) localStorage.setItem(USER_KEY, u);
  if (a) localStorage.setItem(API_KEY, a);
}

/** Remove persisted account key (same-origin as the app). */
export function clearStoredUserId(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(USER_KEY_LEGACY);
}
