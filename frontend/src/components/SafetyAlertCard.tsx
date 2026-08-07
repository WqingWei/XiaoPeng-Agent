import { ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { SafetyAlert, SafetyLevel } from "@/types";

const LEVEL_STYLES: Record<SafetyLevel, string> = {
  L0: "border-emerald-400/25 bg-emerald-400/8 text-emerald-300",
  L1: "border-yellow-400/25 bg-yellow-400/8 text-yellow-300",
  L2: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  L3: "border-red-400/30 bg-red-400/10 text-red-300",
  L4: "animate-pulse border-red-500/50 bg-red-500/15 text-red-200",
};

export function SafetyAlertCard({ alert }: { alert: SafetyAlert }) {
  return (
    <div className={`rounded-xl border p-3 ${LEVEL_STYLES[alert.level]}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold"><ShieldAlert className="size-3.5" />安全等级 {alert.level}</span>
        <Badge className="border-current/20 bg-black/10 text-current" variant="outline">{alert.rule_id}</Badge>
      </div>
      <p className="mt-2 text-xs leading-5 text-current/90">{alert.message}</p>
      <p className="mt-2 text-[10px] text-current/70">处理方：{alert.required_action}</p>
    </div>
  );
}
