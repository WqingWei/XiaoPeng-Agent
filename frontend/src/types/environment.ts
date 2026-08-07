import type { Location } from "@/types/vehicle";

export interface WeatherInfo {
  condition: "sunny" | "cloudy" | "rainy" | "snowy" | "foggy";
  temperature: number;
  humidity: number;
  visibility_km: number;
}

export interface TimeContext {
  current: string;
  period: "morning" | "afternoon" | "evening" | "night";
  is_holiday: boolean;
}

export interface TrafficIncident {
  type: "construction" | "accident" | "closure";
  location: Location;
  description: string;
}

export interface TrafficInfo {
  congestion_level: "low" | "medium" | "high" | "severe";
  incidents: TrafficIncident[];
}

export interface NearbyFacilities {
  charging_stations: Record<string, unknown>[];
  service_areas: Record<string, unknown>[];
  hospitals: Record<string, unknown>[];
  parking_lots: Record<string, unknown>[];
  restaurants: Record<string, unknown>[];
}

export interface EnvironmentContext {
  weather: WeatherInfo;
  time: TimeContext;
  traffic: TrafficInfo;
  nearby: NearbyFacilities;
}
