import Link from "next/link";

import { ClearStoredUserIdButton } from "@/components/oauth/ClearStoredUserIdButton";

export default function OauthCancelPage() {
  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-12">
      <h1 className="text-xl font-semibold text-zinc-100">Sign-in cancelled</h1>
      <p className="mt-3 text-sm text-zinc-400">
        Google sign-in was not completed or was denied. No new account key was saved from this flow.
      </p>
      <ClearStoredUserIdButton />
      <p className="mt-2 text-xs text-zinc-500">
        Clears any saved account key in this browser for GMailAgent.
      </p>
      <Link href="/" className="mt-8 text-sm text-sky-400 hover:underline">
        Back to app
      </Link>
    </div>
  );
}
