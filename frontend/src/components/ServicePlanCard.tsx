import { Check, Clock3 } from "lucide-react";

import type { ServicePlan } from "@/types";

export function ServicePlanCard({ plan }: { plan: ServicePlan }) {
  if (!plan.steps.length) {
    return <p className="rounded-xl border border-white/8 bg-black/15 p-3 text-xs text-muted-foreground">本轮无需调用服务工具。</p>;
  }

  return (
    <div className="space-y-3">
      {plan.summary ? <p className="text-xs leading-5 text-muted-foreground">{plan.summary}</p> : null}
      <ol>
        {plan.steps.map((step, index) => (
          <li key={step.step_id} className="relative flex gap-3 pb-4 last:pb-0">
            {index < plan.steps.length - 1 ? <span className="absolute top-7 bottom-0 left-3 w-px bg-xpeng-green/25" /> : null}
            <span className="relative z-10 grid size-6 shrink-0 place-items-center rounded-full bg-xpeng-green text-primary-foreground">
              <Check className="size-3.5" />
            </span>
            <div className="min-w-0 flex-1 rounded-xl border border-white/8 bg-black/15 p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-medium leading-5">{step.action}</p>
                  <code className="mt-1 inline-block text-[11px] text-xpeng-green">{step.tool}</code>
                </div>
                <span className="inline-flex shrink-0 items-center gap-1 text-[10px] text-muted-foreground">
                  <Clock3 className="size-3" />
                  {step.estimated_duration_s}s
                </span>
              </div>
              {step.dependency ? <p className="mt-2 text-[10px] text-muted-foreground">依赖步骤 {step.dependency}</p> : null}
            </div>
          </li>
        ))}
      </ol>
      <p className="text-right text-[10px] text-muted-foreground">预估总耗时 {plan.total_estimated_time_s}s</p>
    </div>
  );
}
