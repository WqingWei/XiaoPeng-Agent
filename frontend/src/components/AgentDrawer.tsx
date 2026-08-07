"use client";

import { BrainCircuit } from "lucide-react";
import { useEffect } from "react";

import { AgentPanel } from "@/components/AgentPanel";
import { Button } from "@/components/ui/button";
import { useAppStore, useChatStore } from "@/stores";

export function AgentDrawer() {
  const isOpen = useAppStore((state) => state.isAgentDrawerOpen);
  const setOpen = useAppStore((state) => state.setAgentDrawerOpen);
  const response = useChatStore((state) => state.selectedResponse);

  useEffect(() => {
    if (!isOpen) return;

    const mediaQuery = window.matchMedia("(min-width: 1280px)");
    const closeOnDesktop = (event: MediaQueryListEvent) => {
      if (event.matches) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    mediaQuery.addEventListener("change", closeOnDesktop);
    window.addEventListener("keydown", closeOnEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      mediaQuery.removeEventListener("change", closeOnDesktop);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [isOpen, setOpen]);

  return (
    <>
      <Button
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        className="fixed right-4 bottom-14 z-30 gap-2 border border-xpeng-green/35 bg-[#121512]/95 text-xs text-foreground shadow-[0_10px_35px_rgba(0,0,0,0.45)] backdrop-blur hover:bg-[#192019] xl:hidden"
        onClick={() => setOpen(true)}
        variant="outline"
      >
        <BrainCircuit className="size-4 text-xpeng-green" />
        Agent 决策
        {response ? <span className="rounded-full bg-xpeng-green/15 px-1.5 py-0.5 text-[9px] text-xpeng-green">Turn {response.turn_id}</span> : null}
      </Button>

      {isOpen ? (
        <div aria-label="Agent 决策详情" aria-modal="true" className="fixed inset-0 z-50 xl:hidden" role="dialog">
          <button
            aria-label="关闭 Agent 决策详情"
            className="drawer-backdrop-enter absolute inset-0 bg-black/65 backdrop-blur-[2px]"
            onClick={() => setOpen(false)}
            type="button"
          />
          <div className="drawer-panel-enter absolute inset-y-0 right-0 w-[min(92vw,400px)] border-l border-white/10 bg-card shadow-[-20px_0_60px_rgba(0,0,0,0.5)]">
            <AgentPanel onClose={() => setOpen(false)} variant="drawer" />
          </div>
        </div>
      ) : null}
    </>
  );
}
