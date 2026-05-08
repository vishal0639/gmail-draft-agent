/** Returns trimmed user id or throws (for API calls that need an account). */
export function withUserId(uid: string | null | undefined): string {
  if (!uid?.trim()) {
    throw new Error("Add your account key in Settings (from Google sign-in).");
  }
  return uid.trim();
}
