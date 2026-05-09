"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { apiRequest } from "@/lib/api";
import { withUserId } from "@/lib/authHelpers";
import { formatMessageDateTime } from "@/lib/formatMessageDate";
import type { Draft } from "@/lib/types";
import {
  mergeDraft,
  setActiveDraft,
  setBodyEd,
  setDraftsList,
  setIdempotencyKey,
} from "@/store/slices/draftsSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useNotify } from "@/hooks/useNotify";

import { btnPrimary, btnSecondary, card, inputCls } from "./styles";

function DraftMetaLine({ d }: { d: Draft }) {
  return (
    <div className="space-y-1">
      <div className="grid w-full grid-cols-[1fr_auto_1fr] items-start gap-x-2 text-[11px]">
        <span className="justify-self-start font-semibold uppercase tracking-wide text-zinc-300">{d.status}</span>
        <span className="justify-self-center px-2 text-center text-zinc-400" title="Expires">
          <span className="text-zinc-600">Expires </span>
          {d.expires_at ? formatMessageDateTime(d.expires_at) : "—"}
        </span>
        <time
          dateTime={d.created_at}
          className="justify-self-end text-right tabular-nums text-zinc-400"
          title="Created"
        >
          <span className="text-zinc-600">Created </span>
          {formatMessageDateTime(d.created_at)}
        </time>
      </div>
      <p className="text-[10px] text-zinc-600">
        Tone <span className="text-zinc-500">{d.tone}</span>
      </p>
    </div>
  );
}

export function DraftsPanel() {
  const dispatch = useAppDispatch();
  const { toast, onError } = useNotify();
  const userId = useAppSelector((s) => s.session.userId);
  const apiBase = useAppSelector((s) => s.session.apiBase);
  const list = useAppSelector((s) => s.drafts.list);
  const active = useAppSelector((s) => s.drafts.active);
  const bodyEd = useAppSelector((s) => s.drafts.bodyEd);

  const [approvedEditMode, setApprovedEditMode] = useState(false);
  const approvedBaselineRef = useRef<string>("");

  const withUser = useCallback((uid: string | null) => withUserId(uid), []);

  useEffect(() => {
    setApprovedEditMode(false);
  }, [active?.id]);

  const selectDraft = (d: Draft) => {
    if (active?.id === d.id) {
      dispatch(setActiveDraft(null));
      return;
    }
    dispatch(setActiveDraft(d));
  };

  const load = async () => {
    try {
      withUser(userId);
      const d = await apiRequest<{ items: Draft[] }>("/drafts?limit=100", { userId, apiBase });
      const items = d.items || [];
      dispatch(setDraftsList(items));
      if (active?.id) {
        const m = items.find((x) => x.id === active.id);
        if (m) dispatch(setActiveDraft(m));
        else dispatch(setActiveDraft(null));
      }
    } catch (e) {
      onError(e);
    }
  };

  const refreshOne = useCallback(
    async (id: string) => {
      try {
        const d = await apiRequest<Draft>(`/drafts/${id}`, { userId, apiBase });
        dispatch(mergeDraft(d));
      } catch (e) {
        onError(e);
      }
    },
    [userId, apiBase, onError, dispatch],
  );

  const approve = async (id: string) => {
    try {
      withUser(userId);
      const updated = await apiRequest<Draft>(`/drafts/${id}/approve`, { method: "POST", userId, apiBase });
      dispatch(mergeDraft(updated));
      dispatch(setActiveDraft(updated));
      toast("Draft approved. Review, edit if needed, then send.");
      await load();
    } catch (e) {
      onError(e);
    }
  };

  const reject = async (id: string) => {
    try {
      withUser(userId);
      await apiRequest<Draft>(`/drafts/${id}/reject`, { method: "POST", userId, apiBase });
      toast("Draft dismissed.");
      if (active?.id === id) {
        dispatch(setActiveDraft(null));
      }
      await load();
    } catch (e) {
      onError(e);
    }
  };

  const discardApproved = async (id: string) => {
    try {
      withUser(userId);
      await apiRequest<{ message: string }>(`/drafts/${id}`, { method: "DELETE", userId, apiBase });
      toast("Draft removed from the server.");
      if (active?.id === id) {
        dispatch(setActiveDraft(null));
      }
      await load();
    } catch (e) {
      onError(e);
    }
  };

  const saveEdit = async () => {
    if (!active) return;
    try {
      withUser(userId);
      await apiRequest<Draft>(`/drafts/${active.id}`, {
        method: "PATCH",
        userId,
        apiBase,
        body: JSON.stringify({ body: bodyEd, subject: null }),
      });
      toast("Draft saved.");
      await refreshOne(active.id);
      await load();
      if (active.status === "approved") {
        approvedBaselineRef.current = "";
        setApprovedEditMode(false);
      }
    } catch (e) {
      onError(e);
    }
  };

  const enterApprovedEdit = () => {
    if (!active || active.status !== "approved") return;
    approvedBaselineRef.current = bodyEd;
    setApprovedEditMode(true);
  };

  const unsaveApproved = () => {
    dispatch(setBodyEd(approvedBaselineRef.current));
    setApprovedEditMode(false);
  };

  const sendIt = async () => {
    if (!active || active.status !== "approved") return;
    if (approvedEditMode) {
      toast("Save or Unsave your edits before sending.");
      return;
    }
    try {
      withUser(userId);
      // New key every send. Reusing a key (e.g. from Redux after an earlier success) makes the API
      // return idempotent success without calling Gmail again — UI looked "sent" but no new mail.
      const idem = crypto.randomUUID();
      dispatch(setIdempotencyKey(""));
      const res = await apiRequest<{
        idempotent?: boolean;
        gmail_message_id?: string | null;
      }>("/replies/send", {
        method: "POST",
        userId,
        apiBase,
        headers: { "Idempotency-Key": idem },
        body: JSON.stringify({ draft_id: active.id }),
      });
      if (res?.idempotent) {
        toast("No new email — this send was already completed with this idempotency key.");
      } else {
        toast("Message sent.");
      }
      dispatch(setActiveDraft(null));
      await load();
    } catch (e) {
      onError(e);
    }
  };

  const isPending = active?.status === "pending_review";
  const isApproved = active?.status === "approved";
  const canEditBody = Boolean(isPending || (isApproved && approvedEditMode));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <button type="button" onClick={load} className={btnPrimary}>
          Load drafts
        </button>
        <p className="max-w-xl text-xs text-zinc-500">
          Pending: approve within 24 hours of creation (same clock time next day). After approval: send by 48 hours after
          creation. Dismissed drafts are removed 24 hours after you reject. Sending deletes the draft record here.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2 lg:items-start">
        <ul className="max-h-[min(55vh,480px)] space-y-1 overflow-auto rounded-2xl border border-zinc-800 bg-zinc-900/30 p-2">
          {list.length === 0 && <li className="p-4 text-sm text-zinc-500">No drafts yet. Create one from Inbox.</li>}
          {list.map((d) => {
            const selected = active?.id === d.id;
            return (
              <li
                key={d.id}
                className={`rounded-xl border transition-colors ${
                  selected ? "border-violet-500/40 bg-violet-950/15" : "border-transparent hover:bg-zinc-800/30"
                }`}
              >
                <button type="button" onClick={() => selectDraft(d)} className="w-full px-3 py-3 text-left">
                  <DraftMetaLine d={d} />
                  <p className="mt-1 line-clamp-2 font-medium text-zinc-200">{d.subject}</p>
                  {d.error_message ? (
                    <p className="mt-1 line-clamp-2 text-[11px] text-rose-400/90">{d.error_message}</p>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
        {active ? (
          <div className={card + " !p-5 space-y-4 lg:sticky lg:top-4"}>
            <div>
              <p className="text-sm font-medium text-zinc-100">{active.subject}</p>
              <div className="mt-2">
                <DraftMetaLine d={active} />
              </div>
            </div>
            <textarea
              value={bodyEd}
              onChange={(e) => dispatch(setBodyEd(e.target.value))}
              readOnly={!canEditBody}
              rows={14}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950/80 p-3 text-sm text-zinc-100 focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/30 read-only:cursor-default read-only:opacity-95"
            />
            {isPending && (
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={saveEdit} className={btnSecondary}>
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => approve(active.id)}
                  className="rounded-lg bg-emerald-700/90 px-3 py-2 text-sm text-white hover:bg-emerald-600"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => reject(active.id)}
                  className="rounded-lg border border-rose-900/60 bg-rose-950/30 px-3 py-2 text-sm text-rose-300 hover:bg-rose-950/50"
                >
                  Dismiss
                </button>
              </div>
            )}
            {isApproved && !approvedEditMode && (
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={enterApprovedEdit} className={btnSecondary}>
                  Edit
                </button>
                <button type="button" onClick={sendIt} className={btnPrimary}>
                  Send
                </button>
                <button
                  type="button"
                  onClick={() => discardApproved(active.id)}
                  className="rounded-lg border border-zinc-600 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
                >
                  Unsend
                </button>
              </div>
            )}
            {isApproved && approvedEditMode && (
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={saveEdit} className={btnPrimary}>
                  Save
                </button>
                <button type="button" onClick={unsaveApproved} className={btnSecondary}>
                  Unsave
                </button>
              </div>
            )}
            {/* {isApproved && !approvedEditMode && (
              <div>
                <label className="text-xs text-zinc-500">Send idempotency key (optional)</label>
                <input
                  value={idempotencyKey}
                  onChange={(e) => dispatch(setIdempotencyKey(e.target.value))}
                  className={inputCls + " !mt-1 text-xs font-mono"}
                  placeholder="Auto if empty"
                />
              </div>
            )} */}
            {!isPending && !isApproved && (
              <p className="text-xs text-zinc-500">
                {active.status === "failed"
                  ? active.error_message || "Send failed. You can dismiss this draft or create a new one from Inbox."
                  : "This draft is read-only here."}
              </p>
            )}
          </div>
        ) : (
          <div className={`${card} !p-5 text-sm text-zinc-500`}>
            Select a draft from the list to preview and act on it.
          </div>
        )}
      </div>
    </div>
  );
}
