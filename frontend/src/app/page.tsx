"use client";

import { AgentPanel } from "@/components/AgentPanel";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { SceneSelector } from "@/components/SceneSelector";
import { StatusBar } from "@/components/StatusBar";
import { useSocket } from "@/hooks";

export default function Home() {
  useSocket();

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground lg:h-dvh lg:overflow-hidden">
      <Header />
      <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)_400px]">
        <SceneSelector />
        <ChatPanel />
        <AgentPanel />
      </main>
      <StatusBar />
    </div>
  );
}
