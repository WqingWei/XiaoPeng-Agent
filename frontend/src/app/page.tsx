"use client";

import { useSocket } from "@/hooks";
import { useAppStore, useVehicleStore } from "@/stores";

export default function Home() {
  useSocket();

  const mode = useAppStore((state) => state.mode);
  const currentScenario = useAppStore((state) => state.currentScenario);
  const isConnected = useAppStore((state) => state.isConnected);
  const vehicle = useVehicleStore((state) => state.vehicle);

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-card px-5">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="size-2.5 rounded-full bg-xpeng-green shadow-[0_0_18px_var(--xpeng-green)]"
          />
          <div>
            <p className="text-sm font-semibold tracking-wide">
              小鹏 AI 出行服务管家
            </p>
            <p className="text-xs text-muted-foreground">Agent Service Orchestrator</p>
          </div>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted-foreground">
          {mode === "owner" ? "车主自驾模式" : "Robotaxi 模式"}
        </div>
      </header>

      <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)_400px]">
        <aside className="min-h-48 border-b border-white/10 bg-card/70 p-5 lg:border-r lg:border-b-0">
          <PanelHeading eyebrow="SCENARIOS" title="场景选择" />
          <div className="mt-5 rounded-xl border border-dashed border-white/15 bg-white/[0.025] p-4 text-sm leading-6 text-muted-foreground">
            {currentScenario ? `当前场景：${currentScenario}` : "等待选择演示场景"}
          </div>
        </aside>

        <section className="flex min-h-[420px] min-w-0 flex-col bg-background p-5">
          <PanelHeading eyebrow="CONVERSATION" title="对话交互" />
          <div className="mt-5 flex flex-1 items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.015] p-8 text-center">
            <div>
              <p className="text-sm text-foreground/80">对话区域已就绪</p>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                消息列表与输入组件将在第 12 步接入
              </p>
            </div>
          </div>
        </section>

        <aside className="min-h-64 border-t border-white/10 bg-card/70 p-5 lg:border-t-0 lg:border-l">
          <PanelHeading eyebrow="AGENT INSIGHTS" title="决策详情" />
          <div className="mt-5 grid gap-3">
            {[
              "意图分析",
              "服务计划",
              "安全警告",
              "禁止动作",
              "工具调用",
            ].map((label) => (
              <div
                key={label}
                className="rounded-xl border border-white/10 bg-white/[0.025] px-4 py-3 text-sm text-muted-foreground"
              >
                {label}
              </div>
            ))}
          </div>
        </aside>
      </main>

      <footer className="flex min-h-10 shrink-0 flex-wrap items-center gap-x-5 gap-y-1 border-t border-white/10 bg-card px-5 py-2 text-xs text-muted-foreground">
        <StatusItem active={isConnected} label={isConnected ? "Agent 已连接" : "Agent 未连接"} />
        <span>电量 {vehicle ? `${vehicle.battery.level}%` : "--"}</span>
        <span>速度 {vehicle ? `${vehicle.speed} km/h` : "--"}</span>
        <span className="min-w-0 truncate">
          位置 {vehicle?.location.address || "等待车辆状态"}
        </span>
      </footer>
    </div>
  );
}

function PanelHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold tracking-[0.2em] text-xpeng-green">
        {eyebrow}
      </p>
      <h2 className="mt-1 text-base font-semibold">{title}</h2>
    </div>
  );
}

function StatusItem({ active, label }: { active: boolean; label: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden="true"
        className={`size-1.5 rounded-full ${active ? "bg-xpeng-green" : "bg-zinc-600"}`}
      />
      {label}
    </span>
  );
}
