import { create } from "zustand";

import type { VehicleState } from "@/types";

interface VehicleStoreState {
  vehicle: VehicleState | null;
  setVehicle: (vehicle: VehicleState) => void;
  clearVehicle: () => void;
}

export const useVehicleStore = create<VehicleStoreState>((set) => ({
  vehicle: null,
  setVehicle: (vehicle) => set({ vehicle }),
  clearVehicle: () => set({ vehicle: null }),
}));
