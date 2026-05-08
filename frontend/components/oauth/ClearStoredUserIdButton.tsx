"use client";

import { useState } from "react";

import { useAppDispatch } from "@/store/hooks";
import { setUserId } from "@/store/slices/sessionSlice";
import { clearStoredUserId } from "@/lib/sessionStorage";

export function ClearStoredUserIdButton() {
  const dispatch = useAppDispatch();
  const [done, setDone] = useState(false);

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          clearStoredUserId();
          dispatch(setUserId(""));
          setDone(true);
        }}
        className="mt-8 rounded-lg border border-zinc-600 bg-zinc-900 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
      >
        Remove account key from this browser
      </button>
      {done ? (
        <p className="mt-3 text-sm text-emerald-400/90" role="status">
          Account key removed from this browser&apos;s storage.
        </p>
      ) : null}
    </div>
  );
}
