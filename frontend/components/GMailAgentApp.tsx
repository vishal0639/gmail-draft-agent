"use client";

import { Suspense, useEffect } from "react";

import {
  USER_KEY,
  USER_KEY_LEGACY,
  loadApiBase,
  loadUserId,
  persistSession,
} from "@/lib/sessionStorage";
import { setApiBase, setUserId } from "@/store/slices/sessionSlice";
import { setMsg, setTab } from "@/store/slices/uiSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

import { AlertBar } from "./gmail-agent/AlertBar";
import { AppHeader } from "./gmail-agent/AppHeader";
import { DraftsPanel } from "./gmail-agent/DraftsPanel";
import { InboxPanel } from "./gmail-agent/InboxPanel";
import { OverviewPanel } from "./gmail-agent/OverviewPanel";
// import { SettingsPanel } from "./gmail-agent/SettingsPanel";
import { OAuthQuerySync } from "./oauth/OAuthQuerySync";

const OAUTH_POSTMESSAGE_TYPE = "gmail-agent-oauth";

function allowedOauthMessageOrigins(): string[] {
  const out = new Set<string>();
  const bases = [loadApiBase(), process.env.NEXT_PUBLIC_API_BASE_URL];
  for (const b of bases) {
    const t = b?.trim().replace(/\/$/, "");
    if (!t) continue;
    try {
      const u = t.startsWith("http")
        ? new URL(t)
        : new URL(t, typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
      out.add(u.origin);
    } catch {
      /* skip */
    }
  }
  if (typeof window !== "undefined") {
    try {
      out.add(window.location.origin);
    } catch {
      /* skip */
    }
  }
  out.add("http://127.0.0.1:8000");
  out.add("http://localhost:8000");
  return [...out];
}

export default function GMailAgentApp() {
  const dispatch = useAppDispatch();
  const tab = useAppSelector((s) => s.ui.tab);

  useEffect(() => {
    dispatch(setUserId(loadUserId()));
    dispatch(setApiBase(loadApiBase()));
  }, [dispatch]);

  /** When another tab (e.g. /oauth-done) clears the account key, keep Redux in sync. */
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key !== USER_KEY && e.key !== USER_KEY_LEGACY) return;
      dispatch(setUserId(loadUserId()));
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [dispatch]);

  useEffect(() => {
    const onMessage = (ev: MessageEvent) => {
      if (!allowedOauthMessageOrigins().includes(ev.origin)) return;
      const d = ev.data;
      if (!d || d.type !== OAUTH_POSTMESSAGE_TYPE) return;
      if (d.ok && typeof d.userId === "string" && d.userId.trim()) {
        const uid = d.userId.trim();
        dispatch(setUserId(uid));
        persistSession(uid, loadApiBase());
        dispatch(setApiBase(loadApiBase()));
        dispatch(setMsg("Signed in — account key saved on this device."));
        dispatch(setTab("overview"));
        return;
      }
      if (!d.ok) {
        dispatch(setMsg("Google sign-in was cancelled or failed."));
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [dispatch]);

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 pb-24 pt-8 sm:px-6 lg:px-8">
      <Suspense fallback={null}>
        <OAuthQuerySync />
      </Suspense>
      <AppHeader />
      <AlertBar />
      {tab === "overview" && <OverviewPanel />}
      {tab === "inbox" && <InboxPanel />}
      {tab === "drafts" && <DraftsPanel />}
      {/* {tab === "settings" && <SettingsPanel />} */}
      <footer className="mt-20 border-t border-zinc-800/80 pt-8 text-center text-xs text-zinc-600">
        <div className="space-y-1">
          <div className="text-zinc-500">© {2026} Vishal M</div>
          <div className="text-zinc-600">AI-assisted Gmail reply drafts — review, approve, then send.</div>
        </div>
      </footer>
    </div>
  );
}
