function parseMessageDate(raw: string | null | undefined): Date | null {
  if (raw == null || raw === "") return null;
  const trimmed = String(raw).trim();
  const ms = Number(trimmed);
  const d =
    !Number.isNaN(ms) && ms > 0 ? new Date(ms) : new Date(trimmed);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Gmail `internalDate` is milliseconds since epoch as a string. */
export function formatMessageDateTime(raw: string | null | undefined): string {
  const d = parseMessageDate(raw);
  if (!d) return "—";
  const now = new Date();
  const opts: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };
  if (d.getFullYear() !== now.getFullYear()) {
    opts.year = "numeric";
  }
  return d.toLocaleString(undefined, opts);
}

/** For `<time dateTime={…}>` when the value is valid. */
export function messageDateTimeIso(raw: string | null | undefined): string | undefined {
  const d = parseMessageDate(raw);
  return d ? d.toISOString() : undefined;
}
