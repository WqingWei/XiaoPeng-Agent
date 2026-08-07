import { create } from "zustand";

import type { AgentMode } from "@/types";

interface AppState {
  sessionId: string;
  mode: AgentMode;
  currentScenario: string | null;
  isConnected: boolean;
  isAgentDrawerOpen: boolean;
  isAgentPanelCollapsed: boolean;
  isSessionReady: boolean;
  setSessionId: (sessionId: string) => void;
  setMode: (mode: AgentMode) => void;
  setCurrentScenario: (scenarioId: string | null) => void;
  setConnected: (isConnected: boolean) => void;
  setAgentDrawerOpen: (isAgentDrawerOpen: boolean) => void;
  setAgentPanelCollapsed: (isAgentPanelCollapsed: boolean) => void;
  setSessionReady: (isSessionReady: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: "",
  mode: "owner",
  currentScenario: null,
  isConnected: false,
  isAgentDrawerOpen: false,
  isAgentPanelCollapsed: false,
  isSessionReady: false,
  setSessionId: (sessionId) => set({ sessionId }),
  setMode: (mode) => set({ mode }),
  setCurrentScenario: (currentScenario) => set({ currentScenario }),
  setConnected: (isConnected) => set({ isConnected }),
  setAgentDrawerOpen: (isAgentDrawerOpen) => set({ isAgentDrawerOpen }),
  setAgentPanelCollapsed: (isAgentPanelCollapsed) =>
    set({ isAgentPanelCollapsed }),
  setSessionReady: (isSessionReady) => set({ isSessionReady }),
}));
