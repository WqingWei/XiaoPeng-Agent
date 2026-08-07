import type { AgentMode } from "@/types/agent";

export interface Location {
  lat: number;
  lng: number;
  address: string;
}

export interface BatteryInfo {
  level: number;
  range_km: number;
  charging: boolean;
  temperature: number;
}

export interface FuelInfo {
  level: number;
  range_km: number;
}

export type SeatId = "driver" | "passenger" | "rear_left" | "rear_right";

export interface SeatInfo {
  id: SeatId;
  occupied: boolean;
  child_seat: boolean;
}

export interface ACState {
  zone_temp: Record<string, number>;
  fan_speed: number;
  mode: "auto" | "cool" | "heat" | "vent";
}

export interface WindowState {
  front_left: number;
  front_right: number;
  rear_left: number;
  rear_right: number;
}

export interface AmbientLight {
  color: string;
  brightness: number;
}

export interface CabinState {
  ac: ACState;
  seats: SeatInfo[];
  windows: WindowState;
  child_lock: boolean;
  ambient_light: AmbientLight;
}

export interface DriverState {
  fatigue_level: number;
  driving_duration_min: number;
  lane_departure_count: number;
  eyes_detected: boolean;
}

export interface TripInfo {
  start_time: string | null;
  distance_km: number;
  avg_speed: number;
}

export interface VehicleState {
  vehicle_id: string;
  mode: AgentMode;
  driving_status: "parked" | "driving" | "charging";
  speed: number;
  location: Location;
  battery: BatteryInfo;
  fuel: FuelInfo;
  cabin: CabinState;
  driver: DriverState;
  trip: TripInfo;
}

export interface VehicleStateUpdate {
  session_id: string;
  vehicle: VehicleState;
}
