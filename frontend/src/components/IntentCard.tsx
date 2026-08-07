import { Badge } from "@/components/ui/badge";
import type { IntentType, Reasoning } from "@/types";

const INTENT_META: Record<IntentType, { label: string; className: string }> = {
  explicit: { label: "显性意图", className: "border-blue-400/20 bg-blue-400/10 text-blue-300" },
  implicit: { label: "隐性意图", className: "border-orange-400/20 bg-orange-400/10 text-orange-300" },
  urgent: { label: "紧急意图", className: "border-red-400/20 bg-red-400/10 text-red-300" },
};

export function IntentCard({ reasoning }: { reasoning: Reasoning }) {
  const meta = INTENT_META[reasoning.intent_type];
  const confidence = reasoning.confidence;
  const percentage = Math.round(confidence * 100);

  return (
    <div className="space-y-4 rounded-xl border border-white/8 bg-black/15 p-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Badge className={meta.className} variant="outline">{meta.label}</Badge>
        <span className="text-xs text-muted-foreground">
          置信度 {percentage}%
        </span>
      </div>
      <div>
        <p className="text-[11px] text-muted-foreground">识别意图</p>
        <p className="mt-1 text-sm font-medium leading-5">{reasoning.detected_intent || "等待分析"}</p>
      </div>
      <div>
        <div
          aria-label="意图置信度"
          aria-valuemax={100}
          aria-valuemin={0}
          aria-valuenow={percentage}
          className="h-1.5 overflow-hidden rounded-full bg-white/8"
          role="progressbar"
        >
          <div
            className="h-full rounded-full bg-xpeng-green transition-[width]"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
      {reasoning.context_factors.length ? (
        <div>
          <p className="text-[11px] text-muted-foreground">上下文因素</p>
          <ul className="mt-2 space-y-1.5">
            {reasoning.context_factors.map((factor) => (
              <li key={factor} className="flex gap-2 text-xs leading-5 text-foreground/80">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-xpeng-green" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
