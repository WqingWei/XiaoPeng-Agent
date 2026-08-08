import { create } from "zustand";

import type { AgentResponse, ConversationMessage, ThinkingStep } from "@/types";

export type ChatRole = "user" | "assistant" | "system";
export type SceneTransition = "idle" | "exiting" | "entering";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  agentResponse?: AgentResponse;
}

type NewChatMessage = Omit<ChatMessage, "id" | "timestamp"> &
  Partial<Pick<ChatMessage, "id" | "timestamp">>;

interface ChatState {
  messages: ChatMessage[];
  selectedResponse: AgentResponse | null;
  thinkingStep: ThinkingStep | null;
  isProcessing: boolean;
  error: string | null;
  sceneTransition: SceneTransition;
  addMessage: (message: NewChatMessage) => string;
  clearMessages: () => void;
  hydrateMessages: (messages: ConversationMessage[]) => void;
  setSelectedResponse: (response: AgentResponse | null) => void;
  setThinkingStep: (step: ThinkingStep | null) => void;
  setProcessing: (isProcessing: boolean) => void;
  setError: (error: string | null) => void;
  setSceneTransition: (sceneTransition: SceneTransition) => void;
}

function createMessageId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `message-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  selectedResponse: null,
  thinkingStep: null,
  isProcessing: false,
  error: null,
  sceneTransition: "idle",
  addMessage: (message) => {
    const id = message.id ?? createMessageId();
    const nextMessage: ChatMessage = {
      ...message,
      id,
      timestamp: message.timestamp ?? new Date().toISOString(),
    };
    set((state) => ({
      messages: [...state.messages, nextMessage],
      selectedResponse: message.agentResponse ?? state.selectedResponse,
    }));
    return id;
  },
  clearMessages: () =>
    set({
      messages: [],
      selectedResponse: null,
      thinkingStep: null,
      isProcessing: false,
      error: null,
    }),
  hydrateMessages: (messages) => {
    const hydrated = messages
      .filter((message) => message.role !== "system")
      .map((message, index) => ({
        id: `history-${index}-${message.timestamp}`,
        role: message.role,
        content: message.content,
        timestamp: message.timestamp,
        agentResponse: message.agent_response ?? undefined,
      }));
    const selectedResponse = [...hydrated]
      .reverse()
      .find((message) => message.agentResponse)?.agentResponse;
    set({
      messages: hydrated,
      selectedResponse: selectedResponse ?? null,
      thinkingStep: null,
      isProcessing: false,
    });
  },
  setSelectedResponse: (selectedResponse) => set({ selectedResponse }),
  setThinkingStep: (thinkingStep) => set({ thinkingStep }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  setError: (error) => set({ error }),
  setSceneTransition: (sceneTransition) => set({ sceneTransition }),
}));
