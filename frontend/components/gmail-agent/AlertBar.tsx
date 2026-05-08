"use client";

import { dismissAlert } from "@/store/slices/uiSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

export function AlertBar() {
  const dispatch = useAppDispatch();
  const msg = useAppSelector((s) => s.ui.msg);
  const err = useAppSelector((s) => s.ui.err);

  if (!msg && !err) return null;

  return (
    <div
      role="status"
      className={`mb-8 flex items-center justify-between gap-4 rounded-xl border px-4 py-3 text-sm ${
        err
          ? "border-red-900/50 bg-red-950/50 text-red-200"
          : "border-emerald-900/50 bg-emerald-950/40 text-emerald-200"
      }`}
    >
      <span className="min-w-0 flex-1">{err || msg}</span>
      <button
        type="button"
        onClick={() => dispatch(dismissAlert())}
        className="shrink-0 rounded-md px-2 py-1 text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
