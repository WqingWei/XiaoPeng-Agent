import type {
  AgentMode,
  ConversationMessage,
  EnvironmentContext,
  OrderState,
  VehicleState,
} from "@/types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_SOCKET_URL ??
  "http://localhost:8000";

export interface StateSnapshot {
  session_id: string;
  scenario_id: string | null;
  turn_id: number;
  messages: ConversationMessage[];
  vehicle: VehicleState;
  environment: EnvironmentContext;
  order: OrderState | null;
  user_profile: Record<string, unknown>;
}

export interface ScenarioMeta {
  title: string;
  mode: AgentMode;
  description: string;
}

export interface ScenarioSwitchResponse {
  session_id: string;
  scenario_id: string;
  scenario: ScenarioMeta;
  state: StateSnapshot;
}

export interface ModeSwitchResponse {
  session_id: string;
  mode: AgentMode;
  scenario_id: string;
  scenario: ScenarioMeta;
  state: StateSnapshot;
}

export interface ScenarioClearResponse {
  session_id: string;
  scenario_id: null;
  mode: AgentMode;
  state: StateSnapshot;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      payload?.detail?.message ?? payload?.detail ?? payload?.message;
    throw new Error(
      typeof detail === "string" ? detail : `请求失败 (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}

export function switchScenario(
  sessionId: string,
  scenarioId: string,
): Promise<ScenarioSwitchResponse> {
  return request("/api/scenario", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, scenario_id: scenarioId }),
  });
}

export function clearScenario(
  sessionId: string,
): Promise<ScenarioClearResponse> {
  return request(`/api/scenario/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}

export function switchAgentMode(
  sessionId: string,
  mode: AgentMode,
): Promise<ModeSwitchResponse> {
  return request("/api/mode", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, mode }),
  });
}
