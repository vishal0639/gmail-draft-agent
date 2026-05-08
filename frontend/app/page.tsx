import { Suspense } from "react";

import GMailAgentApp from "@/components/GMailAgentApp";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-zinc-950" aria-hidden />}>
      <GMailAgentApp />
    </Suspense>
  );
}
