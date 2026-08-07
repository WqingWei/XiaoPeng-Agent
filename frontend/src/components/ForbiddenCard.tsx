import { Ban } from "lucide-react";

import type { ForbiddenAction } from "@/types";

export function ForbiddenCard({ forbidden }: { forbidden: ForbiddenAction }) {
  return (
    <div className="rounded-xl border border-red-500/30 bg-red-500/8 p-3">
      <div className="flex items-center justify-between gap-2 text-red-300">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold"><Ban className="size-3.5" />{forbidden.action}</span>
        <code className="text-[10px]">{forbidden.rule_id}</code>
      </div>
      <p className="mt-2 text-xs leading-5 text-red-100/75">{forbidden.reason}</p>
    </div>
  );
}
