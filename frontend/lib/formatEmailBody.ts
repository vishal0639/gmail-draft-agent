/** Decode numeric / named HTML entities common in Gmail plain-text bodies. */
export function decodeHtmlEntities(raw: string): string {
  if (typeof window === "undefined") {
    return raw
      .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
      .replace(/&#x([\da-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16)))
      .replace(/&lt;/gi, "<")
      .replace(/&gt;/gi, ">")
      .replace(/&amp;/g, "&")
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/g, "'");
  }
  const el = document.createElement("textarea");
  el.innerHTML = raw;
  return el.value;
}

/**
 * Split Gmail-style plain replies into the latest block vs quoted "On … wrote:" sections.
 */
export function splitGmailQuotedBlocks(text: string): string[] {
  let d = decodeHtmlEntities(text.replace(/\r\n/g, "\n"));
  d = d.replace(/([.!?])\s*(On [^\n]{10,800}?wrote:)/gi, "$1\n\n$2");
  d = d.replace(/(\s)(On [^\n]{10,800}?wrote:)/g, "\n\n$2");
  const parts = d.split(/\n+(?=On [^\n]{10,800}?wrote:\s*\n)/i);
  if (parts.length <= 1) {
    return [d.trim()];
  }
  return parts.map((p) => p.trim()).filter(Boolean);
}
