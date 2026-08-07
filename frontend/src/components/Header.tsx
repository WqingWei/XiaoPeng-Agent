import { Sparkles } from "lucide-react";

import { ModeToggle } from "@/components/ModeToggle";

export function Header() {
  return (
    <header className="flex min-h-16 shrink-0 items-center justify-between gap-4 border-b border-white/10 bg-card px-4 py-3 sm:px-5">
      <div className="flex min-w-0 items-center gap-3">
        <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-xpeng-green text-primary-foreground shadow-[0_0_24px_rgb(0_193_93_/_0.2)]">
          <Sparkles className="size-5" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-semibold tracking-wide sm:text-base">
            小鹏 AI 出行服务管家
          </h1>
          <p className="hidden text-[10px] tracking-[0.16em] text-muted-foreground sm:block">
            SERVICE ORCHESTRATION AGENT
          </p>
        </div>
      </div>
      <ModeToggle />
    </header>
  );
}
