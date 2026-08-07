"use client";

import { useEffect } from "react";

import { getAgentState } from "@/lib/api";
import { createSessionId, getOrCreateSessionId } from "@/lib/session";
import { useAppStore, useChatStore, useVehicleStore } from "@/stores";

export function useSessionBootstrap(): void {
  const setSessionId = useAppStore((state) => state.setSessionId);
  const setSessionReady = useAppStore((state) => state.setSessionReady);
  const setMode = useAppStore((state) => state.setMode);
  const setCurrentScenario = useAppStore((state) => state.setCurrentScenario);
  const hydrateMessages = useChatStore((state) => state.hydrateMessages);
  const setError = useChatStore((state) => state.setError);
  const setSnapshot = useVehicleStore((state) => state.setSnapshot);

  useEffect(() => {
    let cancelled = false;
    let sessionId: string;
    try {
      sessionId = getOrCreateSessionId(window.sessionStorage);
    } catch {
      sessionId = createSessionId();
    }

    setSessionId(sessionId);
    setSessionReady(false);

    void getAgentState(sessionId)
      .then((snapshot) => {
        if (cancelled) return;
        setMode(snapshot.vehicle.mode);
        setCurrentScenario(snapshot.scenario_id);
        setSnapshot(snapshot.vehicle, snapshot.environment);
        hydrateMessages(snapshot.messages);
        setError(null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setError(
          error instanceof Error
            ? `历史恢复失败：${error.message}`
            : "历史恢复失败，请确认后端已启动。",
        );
      })
      .finally(() => {
        if (!cancelled) setSessionReady(true);
      });

    return () => {
      cancelled = true;
    };
  }, [
    hydrateMessages,
    setCurrentScenario,
    setError,
    setMode,
    setSessionId,
    setSessionReady,
    setSnapshot,
  ]);
}
