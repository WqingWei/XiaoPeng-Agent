import type { Location } from "@/types/vehicle";

export interface PassengerInfo {
  user_id: string;
  name: string;
  phone: string;
  location: Location;
}

export interface OrderVehicleInfo {
  vehicle_id: string;
  model: string;
  color: string;
  plate: string;
  location: Location;
}

export interface Route {
  pickup: Location;
  dropoff: Location;
  waypoints: Location[];
  estimated_distance_km: number;
  estimated_duration_min: number;
}

export interface Pricing {
  base_fee: number;
  distance_fee: number;
  time_fee: number;
  total: number;
}

export interface OrderTimestamps {
  created_at: string | null;
  driver_assigned_at: string | null;
  arrived_at: string | null;
  trip_started_at: string | null;
  trip_ended_at: string | null;
}

export type OrderStatus =
  | "pending"
  | "driver_assigned"
  | "arriving"
  | "waiting"
  | "in_trip"
  | "completed"
  | "cancelled";

export interface OrderState {
  order_id: string;
  status: OrderStatus;
  passenger: PassengerInfo;
  vehicle: OrderVehicleInfo;
  route: Route;
  pricing: Pricing;
  timestamps: OrderTimestamps;
}
