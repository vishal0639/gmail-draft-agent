"use client";

import { splitGmailQuotedBlocks } from "@/lib/formatEmailBody";

type Props = {
  text: string;
  /** Scroll area max height (Tailwind arbitrary or class) */
  className?: string;
};

/** Readable plain-text email: decoded entities + quoted replies indented like Gmail. */
export function EmailThreadBody({ text, className }: Props) {
  const blocks = splitGmailQuotedBlocks(text || "");
  const [lead, ...quotes] = blocks.length ? blocks : [""];

  return (
    <div
      className={
        className ??
        "max-h-[min(65vh,560px)] min-h-0 overflow-y-auto overscroll-y-contain rounded-lg border border-zinc-800/90 bg-zinc-950/70 px-3 py-3"
      }
    >
      <div className="space-y-4">
        <div className="whitespace-pre-wrap break-words text-[13px] leading-relaxed text-zinc-200">{lead}</div>
        {quotes.map((q, i) => (
          <blockquote
            key={i}
            className="border-l-2 border-zinc-600/90 pl-3 text-[13px] leading-relaxed text-zinc-400"
          >
            <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-zinc-600">
              Earlier message
            </div>
            <div className="whitespace-pre-wrap break-words">{q}</div>
          </blockquote>
        ))}
      </div>
    </div>
  );
}
