import Link from "next/link";

import { ClearStoredUserIdButton } from "@/components/oauth/ClearStoredUserIdButton";

export default function OauthDonePage() {
  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-12">
      <h1 className="text-xl font-semibold text-zinc-100">Sign-in complete</h1>
      <p className="mt-3 text-sm text-zinc-400">
        Return to the GMailAgent tab to continue. You can close this window.
      </p>
      <ClearStoredUserIdButton />
      <p className="mt-2 text-xs text-zinc-500">
        Use this if you signed in on a shared machine and want to clear the saved key from this device only.
      </p>
      <Link href="/" className="mt-8 text-sm text-sky-400 hover:underline">
        Open app
      </Link>
    </div>
  );
}
