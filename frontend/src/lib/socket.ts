import { io, type Socket } from "socket.io-client";

import type {
  AgentErrorEvent,
  AgentMode,
  AgentResponse,
  AgentThinkingEvent,
  VehicleStateUpdate,
} from "@/types";

interface ServerToClientEvents {
  agent_response: (response: AgentResponse) => void;
  agent_thinking: (event: AgentThinkingEvent) => void;
  vehicle_state_update: (event: VehicleStateUpdate) => void;
  agent_error: (event: AgentErrorEvent) => void;
}

interface ClientToServerEvents {
  chat_message: (payload: {
    session_id: string;
    message: string;
    mode: AgentMode;
  }) => void;
}

export const SOCKET_URL =
  process.env.NEXT_PUBLIC_SOCKET_URL ?? "http://localhost:8000";

export const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io(
  SOCKET_URL,
  {
    autoConnect: false,
    transports: ["websocket", "polling"],
    reconnection: true,
  },
);
