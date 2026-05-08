"use client";

import { setTab } from "@/store/slices/uiSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

import { nav } from "./constants";

export function AppHeader() {
  const dispatch = useAppDispatch();
  const tab = useAppSelector((s) => s.ui.tab);

  return (
    <header className="mb-10 border-b border-zinc-800/80 pb-8">
      <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-violet-300 sm:text-4xl">GMailAgent</h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-zinc-400">
            Read your mail, get suggested replies, edit and approve, then send — nothing goes out without you.
          </p>
        </div>
        <nav className="flex flex-wrap items-center justify-end gap-2" aria-label="Primary">
          {nav.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => dispatch(setTab(id))}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                tab === id
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-900/30"
                  : "border border-zinc-600/80 bg-zinc-900/40 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-800/60"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
