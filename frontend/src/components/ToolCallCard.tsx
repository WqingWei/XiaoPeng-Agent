import { Braces, CircleHelp } from "lucide-react";

import type { ServiceStep, ToolSelectionReason } from "@/types";

export function ToolCallCard({ step, reason }: { step: ServiceStep; reason?: ToolSelectionReason }) {
  return (
    <div className="rounded-xl border border-white/8 bg-black/15 p-3">
      <div className="flex items-center justify-between gap-2">
        <code className="text-xs font-semibold text-xpeng-green">{step.tool}</code>
        <span className="rounded-full bg-xpeng-green/10 px-2 py-0.5 text-[9px] text-xpeng-green">步骤 {step.step_id}</span>
      </div>
      <div className="mt-3">
        <p className="flex items-center gap-1.5 text-[10px] text-muted-foreground"><Braces className="size-3" />调用参数</p>
        <pre className="mt-1.5 overflow-x-auto rounded-lg bg-black/30 p-2 text-[10px] leading-4 text-foreground/80">{JSON.stringify(step.params, null, 2)}</pre>
      </div>
      <div className="mt-3 grid gap-2 text-[11px] leading-4">
        <p><span className="text-muted-foreground">选择理由：</span>{reason?.reason || "后端未提供独立选择理由"}</p>
        <p className="flex items-start gap-1.5 text-muted-foreground"><CircleHelp className="mt-0.5 size-3 shrink-0" />结构化执行结果未包含在当前 AgentResponse 中</p>
      </div>
    </div>
  );
}
