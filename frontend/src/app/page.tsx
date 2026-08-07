"use client";

import { AgentPanel } from "@/components/AgentPanel";
import { AgentDrawer } from "@/components/AgentDrawer";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { SceneSelector } from "@/components/SceneSelector";
import { StatusBar } from "@/components/StatusBar";
import { useSessionBootstrap, useSocket } from "@/hooks";
import { useAppStore } from "@/stores";

export default function Home() {
  useSessionBootstrap();
  useSocket();
  const isAgentPanelCollapsed = useAppStore(
    (state) => state.isAgentPanelCollapsed,
  );

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground lg:h-dvh lg:overflow-hidden">
      <Header />
      <main
        className={`grid min-h-0 flex-1 grid-cols-1 transition-[grid-template-columns] duration-300 lg:grid-cols-[240px_minmax(0,1fr)] ${
          isAgentPanelCollapsed
            ? "xl:grid-cols-[240px_minmax(0,1fr)_48px]"
            : "xl:grid-cols-[240px_minmax(0,1fr)_400px]"
        }`}
      >
        <SceneSelector />
        <ChatPanel />
        <AgentPanel />
      </main>
      <AgentDrawer />
      <StatusBar />
    </div>
  );
}
