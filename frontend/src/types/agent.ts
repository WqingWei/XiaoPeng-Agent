export type AgentMode = "owner" | "robotaxi";
export type IntentType = "explicit" | "implicit" | "urgent";
export type SafetyLevel = "L0" | "L1" | "L2" | "L3" | "L4";
export type SafetyHandler = "agent" | "user" | "system";

export interface ToolCall {
  tool: string;
  params: Record<string, unknown>;
}

export interface ServiceStep extends ToolCall {
  step_id: number;
  action: string;
  dependency: number | null;
  estimated_duration_s: number;
}

export interface ServicePlan {
  summary: string;
  steps: ServiceStep[];
  total_estimated_time_s: number;
}

export interface ToolExecutionResult {
  step_id: number;
  tool: string;
  success: boolean;
  output: Record<string, unknown>;
  error: string | null;
  skipped: boolean;
  duration_ms: number;
}

export interface IntentResult {
  detected_intent: string;
  intent_type: IntentType;
  confidence: number;
  context_factors: string[];
  original_message: string;
  entities: Record<string, unknown>;
}

export interface ToolSelectionReason {
  tool: string;
  reason: string;
}

export interface AlternativeConsidered {
  option: string;
  reason_rejected: string;
}

export interface Reasoning {
  detected_intent: string;
  intent_type: IntentType;
  confidence: number;
  context_factors: string[];
  tool_selection_reasons: ToolSelectionReason[];
  alternatives_considered: AlternativeConsidered[];
}

export interface ConversationMessage {
  role: "system" | "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface SafetyAlert {
  level: SafetyLevel;
  rule_id: string;
  message: string;
  required_action: SafetyHandler;
}

export interface ForbiddenAction {
  action: string;
  rule_id: string;
  reason: string;
}

export interface FollowUp {
  needs_confirmation: boolean;
  confirmation_message: string;
  suggested_replies: string[];
}

export interface AgentResponse {
  timestamp: string;
  session_id: string;
  turn_id: number;
  user_response: string;
  service_plan: ServicePlan;
  tool_results: ToolExecutionResult[];
  reasoning: Reasoning;
  forbidden_actions: ForbiddenAction[];
  safety_alerts: SafetyAlert[];
  follow_up: FollowUp;
}

export type ThinkingStep =
  | "intent_analysis"
  | "safety_check"
  | "orchestrating"
  | "generating";

export interface AgentThinkingEvent {
  session_id: string;
  step: ThinkingStep;
}

export interface AgentErrorEvent {
  code: "invalid_request" | "processing_failed" | string;
  message: string;
  session_id?: string;
  details?: unknown[];
}
