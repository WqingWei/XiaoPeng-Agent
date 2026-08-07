"use client";

import { BatteryCharging, CloudFog, CloudRain, CloudSun, Gauge, MapPin, Snowflake, Sun, type LucideIcon } from "lucide-react";

import { AnimatedNumber } from "@/components/AnimatedNumber";
import { useAppStore, useVehicleStore } from "@/stores";

const WEATHER_ICONS: Record<string, LucideIcon> = {
  sunny: Sun,
  cloudy: CloudSun,
  rainy: CloudRain,
  snowy: Snowflake,
  foggy: CloudFog,
};

const STATUS_LABELS = { parked: "已停车", driving: "行驶中", charging: "充电中" } as const;

export function StatusBar() {
  const isConnected = useAppStore((state) => state.isConnected);
  const vehicle = useVehicleStore((state) => state.vehicle);
  const environment = useVehicleStore((state) => state.environment);
  const WeatherIcon = WEATHER_ICONS[environment?.weather.condition ?? "sunny"] ?? Sun;
  const batteryLevel = vehicle?.battery.level ?? 0;

  return (
    <footer className="grid shrink-0 grid-cols-2 gap-x-4 gap-y-2 border-t border-white/10 bg-card px-4 py-2.5 text-[11px] text-muted-foreground sm:flex sm:min-h-11 sm:items-center sm:px-5">
      <div className="flex min-w-28 items-center gap-2">
        <span className={`size-1.5 rounded-full ${isConnected ? "bg-xpeng-green shadow-[0_0_8px_var(--xpeng-green)]" : "bg-zinc-600"}`} />
        <span>{isConnected ? "Agent 在线" : "Agent 离线"}</span>
      </div>
      <div className="flex min-w-36 items-center gap-2">
        <BatteryCharging className="size-3.5 text-xpeng-green" />
        <AnimatedNumber suffix="%" value={vehicle ? batteryLevel : null} />
        <div aria-label="车辆电量" aria-valuemax={100} aria-valuemin={0} aria-valuenow={batteryLevel} className="h-1 w-16 overflow-hidden rounded-full bg-white/10" role="progressbar">
          <div className="h-full rounded-full bg-xpeng-green transition-[width] duration-500 ease-out" style={{ width: `${batteryLevel}%` }} />
        </div>
      </div>
      <div className="flex items-center gap-2"><Gauge className="size-3.5" /><AnimatedNumber suffix=" km/h" value={vehicle?.speed ?? null} /></div>
      <div className="flex items-center gap-2"><span className="rounded bg-white/6 px-1.5 py-0.5 text-[9px]">{vehicle ? STATUS_LABELS[vehicle.driving_status] : "--"}</span><span>{vehicle?.mode === "robotaxi" ? "Robotaxi" : "车主模式"}</span></div>
      <div className="col-span-2 flex min-w-0 flex-1 items-center gap-2 sm:col-span-1"><MapPin className="size-3.5 shrink-0" /><span className="truncate">{vehicle?.location.address || "等待车辆状态"}</span></div>
      <div className="flex items-center gap-2 sm:ml-auto"><WeatherIcon className="size-3.5" /><AnimatedNumber suffix="°C" value={environment?.weather.temperature ?? null} /></div>
    </footer>
  );
}
