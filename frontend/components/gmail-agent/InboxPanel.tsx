"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { apiRequest } from "@/lib/api";
import { withUserId } from "@/lib/authHelpers";
import { formatMessageDateTime, messageDateTimeIso } from "@/lib/formatMessageDate";
import type { EmailDetail, EmailItem, EmailListResponse } from "@/lib/types";
import {
  appendRows,
  setFilter,
  setNextPageToken,
  setRows,
  setSelected,
  setTone,
  type InboxFilter,
  type ReplyTone,
} from "@/store/slices/inboxSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useNotify } from "@/hooks/useNotify";

import { EmailThreadBody } from "./EmailThreadBody";
import { btnPrimary, card } from "./styles";

function bodyTextForRow(detail: EmailDetail | undefined, row: EmailItem): string {
  const t = detail?.body_text?.trim();
  if (t) return t;
  return row.snippet?.trim() || "";
}

const PAGE_SIZE = 7;

export function InboxPanel() {
  const dispatch = useAppDispatch();
  const { toast, onError } = useNotify();
  const userId = useAppSelector((s) => s.session.userId);
  const apiBase = useAppSelector((s) => s.session.apiBase);
  const filter = useAppSelector((s) => s.inbox.filter);
  const rows = useAppSelector((s) => s.inbox.rows);
  const nextPageToken = useAppSelector((s) => s.inbox.nextPageToken);
  const sel = useAppSelector((s) => s.inbox.selected);
  const tone = useAppSelector((s) => s.inbox.tone);

  const [loadingMore, setLoadingMore] = useState(false);
  const listRef = useRef<HTMLUListElement>(null);
  const sentinelRef = useRef<HTMLLIElement>(null);
  const loadMoreLock = useRef(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detailById, setDetailById] = useState<Record<string, EmailDetail>>({});
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailErr, setDetailErr] = useState<string | null>(null);

  const withUser = useCallback((uid: string | null) => withUserId(uid), []);

  useEffect(() => {
    setDetailById({});
    setDetailErr(null);
  }, [userId]);

  useEffect(() => {
    setDetailErr(null);
    if (!expandedId || !userId) return;
    if (detailById[expandedId]) return;
    const ac = new AbortController();
    (async () => {
      setDetailLoading(true);
      try {
        withUser(userId);
        const d = await apiRequest<EmailDetail>(`/emails/${expandedId}`, {
          userId,
          apiBase,
          signal: ac.signal,
        });
        if (!ac.signal.aborted) setDetailById((prev) => ({ ...prev, [expandedId]: d }));
      } catch (e) {
        if (ac.signal.aborted) return;
        setDetailErr(e instanceof Error ? e.message : "Failed to load full message");
      } finally {
        if (!ac.signal.aborted) setDetailLoading(false);
      }
    })();
    return () => ac.abort();
  }, [expandedId, userId, apiBase, detailById, withUser]);

  useEffect(() => {
    if (expandedId && !rows.some((x) => x.id === expandedId)) {
      setExpandedId(null);
    }
  }, [rows, expandedId]);

  const toggleInboxRow = (r: EmailItem) => {
    setExpandedId((prev) => {
      if (prev === r.id) {
        dispatch(setSelected(null));
        return null;
      }
      dispatch(setSelected(r));
      return r.id;
    });
  };

  const load = async () => {
    try {
      withUser(userId);
      dispatch(setNextPageToken(null));
      const params = new URLSearchParams();
      params.set("filter", filter);
      params.set("max_results", String(PAGE_SIZE));
      const d = await apiRequest<EmailListResponse>(`/emails?${params.toString()}`, { userId, apiBase });
      dispatch(setRows(d.items || []));
      dispatch(setNextPageToken(d.next_page_token ?? null));
      toast(`${d.items?.length || 0} messages loaded.`);
    } catch (e) {
      onError(e);
    }
  };

  const loadMore = useCallback(async () => {
    const token = nextPageToken;
    if (!token || loadMoreLock.current) return;
    loadMoreLock.current = true;
    setLoadingMore(true);
    try {
      withUser(userId);
      const params = new URLSearchParams();
      params.set("filter", filter);
      params.set("max_results", String(PAGE_SIZE));
      params.set("page_token", token);
      const d = await apiRequest<EmailListResponse>(`/emails?${params.toString()}`, { userId, apiBase });
      dispatch(appendRows(d.items || []));
      dispatch(setNextPageToken(d.next_page_token ?? null));
    } catch (e) {
      onError(e);
    } finally {
      loadMoreLock.current = false;
      setLoadingMore(false);
    }
  }, [nextPageToken, userId, filter, apiBase, dispatch, withUser, onError]);

  useEffect(() => {
    const root = listRef.current;
    const target = sentinelRef.current;
    if (!root || !target) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) void loadMore();
      },
      { root, rootMargin: "140px", threshold: 0 },
    );
    obs.observe(target);
    return () => obs.disconnect();
  }, [loadMore]);

  const genDraft = async (messageId: string) => {
    try {
      withUser(userId);
      await apiRequest("/drafts/generate", {
        method: "POST",
        userId,
        apiBase,
        body: JSON.stringify({ source_message_id: messageId, tone, custom_instructions: null }),
      });
      toast("Draft created — open Drafts to review.");
    } catch (e) {
      onError(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filter}
          onChange={(e) => {
            dispatch(setFilter(e.target.value as InboxFilter));
            dispatch(setRows([]));
            dispatch(setNextPageToken(null));
            dispatch(setSelected(null));
            setExpandedId(null);
          }}
          className="rounded-lg border border-zinc-700 bg-zinc-950/80 px-3 py-2 text-sm text-zinc-200"
        >
          <option value="unread">Unread</option>
          <option value="recent">Last 7 days</option>
          <option value="all">Inbox</option>
        </select>
        <button type="button" onClick={load} className={btnPrimary}>
          Refresh
        </button>
        <div className="ml-auto flex items-center gap-2 text-sm text-zinc-400">
          <span>Reply tone</span>
          <select
            value={tone}
            onChange={(e) => dispatch(setTone(e.target.value as ReplyTone))}
            className="rounded-lg border border-zinc-700 bg-zinc-950/80 px-2 py-1.5 text-sm"
          >
            <option value="formal">Formal</option>
            <option value="concise">Concise</option>
            <option value="friendly">Friendly</option>
          </select>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <ul
          ref={listRef}
          className="max-h-[min(60vh,520px)] space-y-1 overflow-auto rounded-2xl border border-zinc-800 bg-zinc-900/30 p-2"
          role="list"
        >
          {rows.length === 0 && <li className="p-5 text-sm text-zinc-500">No messages yet. Connect and refresh.</li>}
          {rows.map((r) => {
            const open = expandedId === r.id;
            const rowDetail = detailById[r.id];
            const bodyStr = bodyTextForRow(rowDetail, r);
            return (
              <li
                key={r.id}
                className={`min-h-0 overflow-hidden rounded-xl border text-sm transition ${
                  open ? "border-violet-500/40 bg-violet-950/15" : "border-transparent hover:bg-zinc-800/30"
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggleInboxRow(r)}
                  className="flex w-full gap-3 px-3 py-3 text-left"
                  aria-expanded={open}
                >
                  <div className="min-w-0 flex-1">
                    <p className={`font-medium text-zinc-100 ${open ? "" : "line-clamp-1"}`}>
                      {r.subject || "(No subject)"}
                    </p>
                    <p className="line-clamp-1 text-xs text-zinc-500">{r.from_addr}</p>
                    {!open ? <p className="line-clamp-1 text-xs text-zinc-600">{r.snippet}</p> : null}
                  </div>
                  <time
                    dateTime={messageDateTimeIso(r.internal_date)}
                    className="shrink-0 self-start pt-0.5 text-right text-[11px] tabular-nums text-zinc-500"
                  >
                    {formatMessageDateTime(r.internal_date)}
                  </time>
                </button>
                {open ? (
                  <div className="min-h-0 border-t border-zinc-800/80 bg-black/20 px-3 pb-3 pt-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="min-w-0 flex-1 text-sm font-medium text-zinc-100">
                        {r.subject || "(No subject)"}
                      </p>
                      <time
                        dateTime={messageDateTimeIso(r.internal_date)}
                        className="shrink-0 text-right text-[11px] tabular-nums text-zinc-500"
                      >
                        {formatMessageDateTime(r.internal_date)}
                      </time>
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">{r.from_addr}</p>
                    {open && detailLoading && !rowDetail ? (
                      <p className="mt-2 text-xs text-zinc-500" aria-live="polite">
                        Loading full message…
                      </p>
                    ) : null}
                    {detailErr && open && expandedId === r.id ? (
                      <p className="mt-1 text-xs text-amber-400/90" role="alert">
                        {detailErr} (showing preview only)
                      </p>
                    ) : null}
                    <div
                      className="mt-2 min-h-0"
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                      role="presentation"
                    >
                      <EmailThreadBody text={bodyStr || "(No body)"} />
                    </div>
                  </div>
                ) : null}
              </li>
            );
          })}
          {loadingMore ? (
            <li className="py-2 text-center text-xs text-zinc-500" aria-live="polite">
              Loading more…
            </li>
          ) : null}
          {rows.length > 0 && !nextPageToken && !loadingMore ? (
            <li className="py-2 text-center text-[11px] text-zinc-600">No more messages in this view.</li>
          ) : null}
          <li ref={sentinelRef} className="h-2 list-none" aria-hidden />
        </ul>
        <div className={`${card} !p-5`}>
          {sel ? (
            <div className="flex min-h-0 flex-col">
              <h3 className="text-sm font-medium text-zinc-200">Selected message</h3>
              <div className="mt-2 flex items-start justify-between gap-2">
                <p className="min-w-0 flex-1 text-sm font-medium text-zinc-100">{sel.subject || "(No subject)"}</p>
                <time
                  dateTime={messageDateTimeIso(sel.internal_date)}
                  className="shrink-0 text-right text-[11px] tabular-nums text-zinc-500"
                >
                  {formatMessageDateTime(sel.internal_date)}
                </time>
              </div>
              <p className="mt-1 text-xs text-zinc-500">{sel.from_addr}</p>
              {detailLoading && !detailById[sel.id] ? (
                <p className="mt-2 text-xs text-zinc-500">Loading full message…</p>
              ) : null}
              {detailErr && expandedId === sel.id ? (
                <p className="mt-1 text-xs text-amber-400/90">{detailErr}</p>
              ) : null}
              <div className="mt-3 min-h-0">
                <EmailThreadBody text={bodyTextForRow(detailById[sel.id], sel)} />
              </div>
              <button type="button" onClick={() => genDraft(sel.id)} className={`${btnPrimary} mt-5 w-full sm:w-auto`}>
                Suggest reply draft
              </button>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Select a message to generate a reply draft.</p>
          )}
        </div>
      </div>
    </div>
  );
}
