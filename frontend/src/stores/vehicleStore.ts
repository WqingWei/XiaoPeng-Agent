import { create } from "zustand";

import type { EnvironmentContext, VehicleState } from "@/types";

interface VehicleStoreState {
  vehicle: VehicleState | null;
  environment: EnvironmentContext | null;
  setVehicle: (vehicle: VehicleState) => void;
  setEnvironment: (environment: EnvironmentContext) => void;
  setSnapshot: (vehicle: VehicleState, environment: EnvironmentContext) => void;
  clearVehicle: () => void;
}

export const useVehicleStore = create<VehicleStoreState>((set) => ({
  vehicle: null,
  environment: null,
  setVehicle: (vehicle) => set({ vehicle }),
  setEnvironment: (environment) => set({ environment }),
  setSnapshot: (vehicle, environment) => set({ vehicle, environment }),
  clearVehicle: () => set({ vehicle: null, environment: null }),
}));
