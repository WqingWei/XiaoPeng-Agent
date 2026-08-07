"use client";

import { CarFront, LoaderCircle, Route } from "lucide-react";
import { useState } from "react";

import { switchAgentMode } from "@/lib/api";
import { useAppStore, useChatStore, useVehicleStore } from "@/stores";
import type { AgentMode } from "@/types";

const OPTIONS: Array<{
  value: AgentMode;
  label: string;
  icon: typeof CarFront;
}> = [
  { value: "owner", label: "车主自驾", icon: CarFront },
  { value: "robotaxi", label: "Robotaxi", icon: Route },
];

export function ModeToggle() {
  const sessionId = useAppStore((state) => state.sessionId);
  const mode = useAppStore((state) => state.mode);
  const setMode = useAppStore((state) => state.setMode);
  const setError = useChatStore((state) => state.setError);
  const setSnapshot = useVehicleStore((state) => state.setSnapshot);
  const [pendingMode, setPendingMode] = useState<AgentMode | null>(null);

  async function handleChange(nextMode: AgentMode) {
    if (nextMode === mode || pendingMode) return;
    setPendingMode(nextMode);
    setError(null);
    try {
      const response = await switchAgentMode(sessionId, nextMode);
      setMode(response.mode);
      setSnapshot(response.state.vehicle, response.state.environment);
    } catch (error) {
      setError(error instanceof Error ? error.message : "模式切换失败，请稍后重试。");
    } finally {
      setPendingMode(null);
    }
  }

  return (
    <div
      aria-label="出行模式"
      className="flex rounded-xl border border-white/10 bg-black/25 p-1"
      role="group"
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const active = mode === value;
        const pending = pendingMode === value;
        return (
          <button
            key={value}
            aria-pressed={active}
            className={`inline-flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-xs font-medium transition-colors sm:px-3 ${
              active
                ? "bg-xpeng-green text-primary-foreground"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
            }`}
            disabled={pendingMode !== null}
            onClick={() => void handleChange(value)}
            type="button"
          >
            {pending ? <LoaderCircle className="size-3.5 animate-spin" /> : <Icon className="size-3.5" />}
            <span className="hidden sm:inline">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
