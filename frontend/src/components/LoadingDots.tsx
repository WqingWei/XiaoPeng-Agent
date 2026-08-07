import type { ThinkingStep } from "@/types";

const STEP_LABELS: Record<ThinkingStep, string> = {
  intent_analysis: "正在分析意图...",
  safety_check: "正在检查安全规则...",
  orchestrating: "正在编排服务...",
  generating: "正在生成回复...",
};

export function LoadingDots({ step }: { step: ThinkingStep | null }) {
  return (
    <div aria-live="polite" className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="flex items-center gap-1" aria-hidden="true">
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className="size-1.5 animate-bounce rounded-full bg-xpeng-green"
            style={{ animationDelay: `${index * 120}ms` }}
          />
        ))}
      </span>
      <span>{step ? STEP_LABELS[step] : "Agent 正在思考..."}</span>
    </div>
  );
}
