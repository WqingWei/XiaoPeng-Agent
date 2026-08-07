import { create } from "zustand";

import type { AgentMode } from "@/types";

interface AppState {
  sessionId: string;
  mode: AgentMode;
  currentScenario: string | null;
  isConnected: boolean;
  isAgentDrawerOpen: boolean;
  isAgentPanelCollapsed: boolean;
  setSessionId: (sessionId: string) => void;
  setMode: (mode: AgentMode) => void;
  setCurrentScenario: (scenarioId: string | null) => void;
  setConnected: (isConnected: boolean) => void;
  setAgentDrawerOpen: (isAgentDrawerOpen: boolean) => void;
  setAgentPanelCollapsed: (isAgentPanelCollapsed: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: "xpeng-demo-session",
  mode: "owner",
  currentScenario: null,
  isConnected: false,
  isAgentDrawerOpen: false,
  isAgentPanelCollapsed: false,
  setSessionId: (sessionId) => set({ sessionId }),
  setMode: (mode) => set({ mode }),
  setCurrentScenario: (currentScenario) => set({ currentScenario }),
  setConnected: (isConnected) => set({ isConnected }),
  setAgentDrawerOpen: (isAgentDrawerOpen) => set({ isAgentDrawerOpen }),
  setAgentPanelCollapsed: (isAgentPanelCollapsed) =>
    set({ isAgentPanelCollapsed }),
}));
