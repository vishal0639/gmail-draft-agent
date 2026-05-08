"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { loadApiBase, persistSession } from "@/lib/sessionStorage";
import { setApiBase, setUserId } from "@/store/slices/sessionSlice";
import { setMsg, setTab } from "@/store/slices/uiSlice";
import { useAppDispatch } from "@/store/hooks";

/** Handles ?oauth=1&user_id=… when the OAuth flow had no window.opener (must sit under Suspense). */
export function OAuthQuerySync() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const oauthReturnLock = useRef(false);

  useEffect(() => {
    if (searchParams.get("oauth") !== "1") return;
    const uid = searchParams.get("user_id")?.trim();
    if (!uid || oauthReturnLock.current) return;
    oauthReturnLock.current = true;
    dispatch(setUserId(uid));
    persistSession(uid, loadApiBase());
    dispatch(setApiBase(loadApiBase()));
    dispatch(setMsg("Signed in — account key saved on this device."));
    dispatch(setTab("overview"));
    router.replace("/", { scroll: false });
  }, [searchParams, dispatch, router]);

  return null;
}
