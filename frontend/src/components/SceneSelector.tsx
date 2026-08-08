"use client";

import {
  Baby,
  BatteryCharging,
  Brain,
  BriefcaseBusiness,
  Construction,
  CircleX,
  LoaderCircle,
  MapPin,
  Route,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { clearScenario, switchScenario } from "@/lib/api";
import { useAppStore, useChatStore, useVehicleStore } from "@/stores";
import type { AgentMode } from "@/types";

interface ScenarioItem {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  mode: AgentMode;
  core?: boolean;
}

const SCENARIOS: ScenarioItem[] = [
  {
    id: "fatigue_driving",
    name: "疲劳驾驶",
    description: "主动识别疲劳风险",
    icon: Brain,
    mode: "owner",
    core: true,
  },
  {
    id: "parent_child",
    name: "亲子出行",
    description: "儿童安全与舒适",
    icon: Baby,
    mode: "owner",
    core: true,
  },
  {
    id: "long_distance_charging",
    name: "长途补能",
    description: "续航与充电规划",
    icon: BatteryCharging,
    mode: "owner",
    core: true,
  },
  {
    id: "commute_arrival",
    name: "通勤到达",
    description: "停车与到达准备",
    icon: BriefcaseBusiness,
    mode: "owner",
  },
  {
    id: "robotaxi_cant_find_car",
    name: "找不到车",
    description: "定位并引导乘客",
    icon: MapPin,
    mode: "robotaxi",
  },
  {
    id: "pickup_abnormal",
    name: "上车点异常",
    description: "安全位置替代方案",
    icon: Construction,
    mode: "robotaxi",
  },
  {
    id: "change_destination",
    name: "临时改目的地",
    description: "评估费用与路线",
    icon: Route,
    mode: "robotaxi",
  },
  {
    id: "passenger_help",
    name: "乘客求助",
    description: "最高优先级响应",
    icon: ShieldAlert,
    mode: "robotaxi",
    core: true,
  },
];

export function SceneSelector() {
  const sessionId = useAppStore((state) => state.sessionId);
  const isSessionReady = useAppStore((state) => state.isSessionReady);
  const mode = useAppStore((state) => state.mode);
  const currentScenario = useAppStore((state) => state.currentScenario);
  const setCurrentScenario = useAppStore((state) => state.setCurrentScenario);
  const setMode = useAppStore((state) => state.setMode);
  const hydrateMessages = useChatStore((state) => state.hydrateMessages);
  const setError = useChatStore((state) => state.setError);
  const setSceneTransition = useChatStore((state) => state.setSceneTransition);
  const setSnapshot = useVehicleStore((state) => state.setSnapshot);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const visibleScenarios = SCENARIOS.filter(
    (scenario) => scenario.mode === mode,
  );

  async function handleSelect(scenario: ScenarioItem) {
    if (!isSessionReady || loadingId) return;
    setLoadingId(scenario.id);
    setError(null);
    setSceneTransition("exiting");
    try {
      const [response] = await Promise.all([
        switchScenario(sessionId, scenario.id),
        new Promise((resolve) => window.setTimeout(resolve, 180)),
      ]);
      setCurrentScenario(response.scenario_id);
      setMode(response.scenario.mode);
      setSnapshot(response.state.vehicle, response.state.environment);
      hydrateMessages(response.state.messages);
      setSceneTransition("entering");
      await new Promise((resolve) => window.setTimeout(resolve, 300));
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "场景加载失败，请稍后重试。",
      );
    } finally {
      setSceneTransition("idle");
      setLoadingId(null);
    }
  }

  async function handleClear() {
    if (!isSessionReady || loadingId || !currentScenario) return;
    setLoadingId("clear");
    setError(null);
    setSceneTransition("exiting");
    try {
      const [response] = await Promise.all([
        clearScenario(sessionId),
        new Promise((resolve) => window.setTimeout(resolve, 180)),
      ]);
      setCurrentScenario(null);
      setMode(response.mode);
      setSnapshot(response.state.vehicle, response.state.environment);
      hydrateMessages(response.state.messages);
      setSceneTransition("entering");
      await new Promise((resolve) => window.setTimeout(resolve, 300));
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "取消场景失败，请稍后重试。",
      );
    } finally {
      setSceneTransition("idle");
      setLoadingId(null);
    }
  }

  return (
    <aside className="flex min-h-0 flex-col border-b border-white/10 bg-card/70 lg:border-r lg:border-b-0">
      <div className="px-4 pt-5 pb-3">
        <p className="text-[10px] font-semibold tracking-[0.2em] text-xpeng-green">
          SCENARIOS
        </p>
        <div className="mt-1 flex items-center justify-between gap-2">
          <h2 className="text-base font-semibold">演示场景</h2>
          {currentScenario ? (
            <button
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground disabled:opacity-50"
              disabled={!isSessionReady || loadingId !== null}
              onClick={() => void handleClear()}
              type="button"
            >
              {loadingId === "clear" ? (
                <LoaderCircle className="size-3 animate-spin" />
              ) : (
                <CircleX className="size-3" />
              )}
              取消选择
            </button>
          ) : null}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {mode === "owner" ? "车主自驾" : "Robotaxi"}场景 ·
          选择预设状态快速体验
        </p>
      </div>
      <nav
        aria-label="演示场景"
        className="grid gap-1.5 overflow-y-auto px-3 pb-4 sm:grid-cols-2 lg:grid-cols-1"
      >
        {visibleScenarios.map((scenario) => {
          const Icon = scenario.icon;
          const active = currentScenario === scenario.id;
          const loading = loadingId === scenario.id;
          return (
            <button
              key={scenario.id}
              aria-pressed={active}
              className={`group flex min-w-0 items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors ${
                active
                  ? "border-xpeng-green/50 bg-xpeng-green/10"
                  : "border-transparent hover:border-white/10 hover:bg-white/[0.035]"
              }`}
              disabled={!isSessionReady || loadingId !== null}
              onClick={() => void handleSelect(scenario)}
              type="button"
            >
              <span
                className={`grid size-8 shrink-0 place-items-center rounded-lg ${active ? "bg-xpeng-green text-primary-foreground" : "bg-white/5 text-muted-foreground group-hover:text-foreground"}`}
              >
                {loading ? (
                  <LoaderCircle className="size-4 animate-spin" />
                ) : (
                  <Icon className="size-4" />
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5">
                  <span className="truncate text-sm font-medium">
                    {scenario.name}
                  </span>
                  {scenario.core ? (
                    <Badge className="h-4 px-1.5 text-[9px]">核心</Badge>
                  ) : null}
                </span>
                <span className="block truncate text-[11px] text-muted-foreground">
                  {scenario.description}
                </span>
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
