"use client";

import { useCallback } from "react";

import { apiRequest, resolveApiBase } from "@/lib/api";
import { withUserId } from "@/lib/authHelpers";
import type { UserPreferences } from "@/lib/types";
import { persistSession } from "@/lib/sessionStorage";
import { setApiBase, setUserId } from "@/store/slices/sessionSlice";
import { setPreferences } from "@/store/slices/settingsSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useNotify } from "@/hooks/useNotify";

import { btnPrimary, btnSecondary, card, inputCls, labelCls } from "./styles";

export function SettingsPanel() {
  const dispatch = useAppDispatch();
  const { toast, onError } = useNotify();
  const userId = useAppSelector((s) => s.session.userId);
  const apiBase = useAppSelector((s) => s.session.apiBase);
  const prefs = useAppSelector((s) => s.settings.preferences);

  const withUser = useCallback((uid: string | null) => withUserId(uid), []);

  const saveSession = () => {
    persistSession(userId, apiBase);
    toast("Saved on this device.");
  };

  const load = async () => {
    try {
      withUser(userId);
      const p = await apiRequest<UserPreferences>("/preferences", { userId, apiBase });
      dispatch(setPreferences(p));
    } catch (e) {
      onError(e);
    }
  };

  const savePrefs = async () => {
    if (!prefs) return;
    try {
      withUser(userId);
      await apiRequest("/preferences", {
        method: "PUT",
        userId,
        apiBase,
        body: JSON.stringify({
          default_tone: prefs.default_tone,
          email_signature: prefs.email_signature,
          other: prefs.other,
        }),
      });
      toast("Preferences saved.");
    } catch (e) {
      onError(e);
    }
  };

  const revoke = async () => {
    try {
      withUser(userId);
      await apiRequest("/auth/revoke", { method: "POST", userId, apiBase });
      toast("Google access removed on the server. Sign in again to reconnect.");
    } catch (e) {
      onError(e);
    }
  };

  return (
    <div className="mx-auto max-w-lg space-y-5">
      <div className={card}>
        <h2 className="text-sm font-medium text-zinc-200">Backend URL</h2>
        <p className="mt-1 text-xs text-zinc-500">This device calls: {resolveApiBase(apiBase)}</p>
        <label className={`${labelCls} mt-4`}>Override URL</label>
        <input
          value={apiBase}
          onChange={(e) => dispatch(setApiBase(e.target.value))}
          className={inputCls}
          placeholder="http://127.0.0.1:8000/api/v1"
        />
        <label className={`${labelCls} mt-4`}>Account key</label>
        <input
          value={userId}
          onChange={(e) => dispatch(setUserId(e.target.value))}
          className={inputCls + " font-mono text-xs"}
        />
        <button type="button" onClick={saveSession} className={`${btnPrimary} mt-4`}>
          Save
        </button>
      </div>
      <div className={card}>
        <h2 className="text-sm font-medium text-zinc-200">Reply style</h2>
        <p className="mt-1 text-xs text-zinc-500">Default tone and signature for suggested drafts</p>
        <button type="button" onClick={load} className="mt-3 text-sm text-violet-400 hover:text-violet-300">
          Load current
        </button>
        {prefs && (
          <div className="mt-3 space-y-3">
            <input
              value={prefs.default_tone}
              onChange={(e) => dispatch(setPreferences({ ...prefs, default_tone: e.target.value }))}
              className={inputCls}
            />
            <textarea
              value={prefs.email_signature}
              onChange={(e) => dispatch(setPreferences({ ...prefs, email_signature: e.target.value }))}
              rows={4}
              className={inputCls + " min-h-[100px]"}
            />
            <button type="button" onClick={savePrefs} className={btnPrimary}>
              Update preferences
            </button>
          </div>
        )}
      </div>
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/20 p-5">
        <h2 className="text-sm font-medium text-zinc-200">Sign out of Google (API)</h2>
        <p className="mt-1 text-xs text-zinc-500">Stops this app from using your Gmail access until you sign in again.</p>
        <button
          type="button"
          onClick={revoke}
          className={`${btnSecondary} mt-4 w-full text-rose-300/90 border-rose-900/50 hover:bg-rose-950/30`}
        >
          Revoke access
        </button>
      </div>
    </div>
  );
}
