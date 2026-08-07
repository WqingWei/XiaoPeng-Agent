import { Braces, CheckCircle2, CircleX, SkipForward } from "lucide-react";

import type { ServiceStep, ToolExecutionResult, ToolSelectionReason } from "@/types";

export function ToolCallCard({ step, reason, result, index = 0 }: { step: ServiceStep; reason?: ToolSelectionReason; result?: ToolExecutionResult; index?: number }) {
  const status = result?.skipped ? "已跳过" : result?.success ? "执行成功" : "执行失败";
  const StatusIcon = result?.skipped ? SkipForward : result?.success ? CheckCircle2 : CircleX;
  const statusClass = result?.skipped ? "text-yellow-300" : result?.success ? "text-xpeng-green" : "text-red-300";
  return (
    <div className="tool-step-enter rounded-xl border border-white/8 bg-black/15 p-3" style={{ animationDelay: `${index * 90}ms` }}>
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
        {result ? (
          <div className="space-y-2">
            <p className={`flex items-center gap-1.5 ${statusClass}`}><StatusIcon className="size-3.5" />{status} · {result.duration_ms.toFixed(1)}ms</p>
            {Object.keys(result.output).length ? <pre className="overflow-x-auto rounded-lg bg-black/30 p-2 text-[10px] leading-4 text-foreground/80">{JSON.stringify(result.output, null, 2)}</pre> : null}
            {result.error ? <p className="text-red-300">{result.error}</p> : null}
          </div>
        ) : <p className="text-muted-foreground">未找到对应的执行结果</p>}
      </div>
    </div>
  );
}
