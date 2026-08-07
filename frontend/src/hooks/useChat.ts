"use client";

import { useCallback } from "react";

import { socket } from "@/lib/socket";
import { useAppStore, useChatStore } from "@/stores";

export interface UseChatResult {
  sendMessage: (text: string) => boolean;
}

export function useChat(): UseChatResult {
  const sessionId = useAppStore((state) => state.sessionId);
  const mode = useAppStore((state) => state.mode);
  const addMessage = useChatStore((state) => state.addMessage);
  const setProcessing = useChatStore((state) => state.setProcessing);
  const setThinkingStep = useChatStore((state) => state.setThinkingStep);
  const setError = useChatStore((state) => state.setError);

  const sendMessage = useCallback(
    (text: string) => {
      const message = text.trim();
      if (!message) return false;

      addMessage({ role: "user", content: message });
      setError(null);
      setThinkingStep("intent_analysis");
      setProcessing(true);
      socket.emit("chat_message", { session_id: sessionId, message, mode });
      return true;
    },
    [
      addMessage,
      mode,
      sessionId,
      setError,
      setProcessing,
      setThinkingStep,
    ],
  );

  return { sendMessage };
}
