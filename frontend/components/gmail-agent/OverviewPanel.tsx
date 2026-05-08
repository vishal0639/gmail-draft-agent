"use client";

import { useState } from "react";

import { apiRequest } from "@/lib/api";
import { clearStoredUserId } from "@/lib/sessionStorage";
import type { GoogleAuthUrl } from "@/lib/types";
import { setHealth } from "@/store/slices/overviewSlice";
import { setUserId } from "@/store/slices/sessionSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useNotify } from "@/hooks/useNotify";

import { btnPrimary, btnSecondary, card } from "./styles";

export function OverviewPanel() {
  const dispatch = useAppDispatch();
  const { toast, onError } = useNotify();
  const userId = useAppSelector((s) => s.session.userId);
  const apiBase = useAppSelector((s) => s.session.apiBase);
  const health = useAppSelector((s) => s.overview.health);
  const [oauthFallbackUrl, setOauthFallbackUrl] = useState<string | null>(null);

  const getAuthUrl = async () => {
    try {
      setOauthFallbackUrl(null);
      const d = await apiRequest<GoogleAuthUrl>("/auth/google", { apiBase });
      // Must not use noopener: OAuth callback uses postMessage to window.opener.
      const w = window.open(d.url, "_blank");
      if (w) {
        toast("Google sign-in opened in a new tab. When you finish, this page saves your session automatically.");
      } else {
        setOauthFallbackUrl(d.url);
        toast("Pop-up blocked — open the link below to sign in.");
      }
    } catch (e) {
      onError(e);
    }
  };

  const checkGmail = async () => {
    try {
      const d = await apiRequest<Record<string, unknown>>("/auth/gmail/health", { userId, apiBase });
      dispatch(setHealth(d));
      toast("Connection check finished.");
    } catch (e) {
      onError(e);
    }
  };

  const clearKey = () => {
    clearStoredUserId();
    dispatch(setUserId(""));
    dispatch(setHealth(null));
    toast("Account key removed from this browser.");
  };

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <section className={`${card} lg:col-span-3`}>
        <h2 className="text-lg font-medium text-zinc-100">Connect Gmail</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">
          We use Google&apos;s sign-in. When you finish in the other tab, your <strong className="text-zinc-300">account key</strong> is saved on this
          device automatically — nothing to paste here. If something didn&apos;t sync, remove the key and sign in again.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <button type="button" onClick={getAuthUrl} className={btnPrimary}>
            Start Google sign-in
          </button>
          <button type="button" onClick={checkGmail} className={btnSecondary}>
            Test connection
          </button>
          {userId ? (
            <button type="button" onClick={clearKey} className={btnSecondary}>
              Remove account key
            </button>
          ) : null}
        </div>
        {userId ? (
        <p className="mt-4 text-sm text-emerald-400/90">This browser has an account key saved — use Test connection to verify Gmail access.</p>
        ) : null}
        {oauthFallbackUrl && (
          <div className="mt-5 rounded-xl border border-amber-900/40 bg-amber-950/20 p-4">
            <p className="text-xs text-amber-200/90">Your browser blocked the new tab. Open this link to sign in:</p>
            <a
              href={oauthFallbackUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-1 block break-all text-sm text-violet-400 hover:text-violet-300"
            >
              {oauthFallbackUrl}
            </a>
            <p className="mt-3 text-xs text-amber-200/70">
              If this page doesn&apos;t update after sign-in, refresh the page.
            </p>
          </div>
        )}
        {health && (
          <pre className="mt-4 max-h-40 overflow-auto rounded-lg border border-zinc-800 bg-black/30 p-3 text-xs text-emerald-400/90">
            {JSON.stringify(health, null, 2)}
          </pre>
        )}
      </section>
      <aside className={`${card} lg:col-span-2`}>
        <h2 className="text-sm font-medium text-zinc-200">How it works</h2>
        <ol className="mt-4 space-y-4 text-sm text-zinc-400">
          <li className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-600/20 text-xs font-semibold text-violet-300">
              1
            </span>
            <span>
              Connect Gmail, then open <strong className="text-zinc-300">Inbox</strong> to load messages.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-600/20 text-xs font-semibold text-violet-300">
              2
            </span>
            <span>
              Pick an email, choose a tone, and create a <strong className="text-zinc-300">draft</strong> to review.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-600/20 text-xs font-semibold text-violet-300">
              3
            </span>
            <span>
              Approve (or edit) in <strong className="text-zinc-300">Drafts</strong> — only then can you send.
            </span>
          </li>
        </ol>
      </aside>
    </div>
  );
}
