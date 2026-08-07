import { create } from "zustand";

import type { AgentResponse, ThinkingStep } from "@/types";

export type ChatRole = "user" | "assistant" | "system";

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
  thinkingStep: ThinkingStep | null;
  isProcessing: boolean;
  error: string | null;
  addMessage: (message: NewChatMessage) => string;
  clearMessages: () => void;
  setThinkingStep: (step: ThinkingStep | null) => void;
  setProcessing: (isProcessing: boolean) => void;
  setError: (error: string | null) => void;
}

function createMessageId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `message-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  thinkingStep: null,
  isProcessing: false,
  error: null,
  addMessage: (message) => {
    const id = message.id ?? createMessageId();
    const nextMessage: ChatMessage = {
      ...message,
      id,
      timestamp: message.timestamp ?? new Date().toISOString(),
    };
    set((state) => ({ messages: [...state.messages, nextMessage] }));
    return id;
  },
  clearMessages: () =>
    set({ messages: [], thinkingStep: null, isProcessing: false, error: null }),
  setThinkingStep: (thinkingStep) => set({ thinkingStep }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  setError: (error) => set({ error }),
}));
