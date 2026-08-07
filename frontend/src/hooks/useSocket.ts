"use client";

import { useEffect } from "react";

import { socket } from "@/lib/socket";
import { useAppStore, useChatStore, useVehicleStore } from "@/stores";
import type {
  AgentErrorEvent,
  AgentResponse,
  AgentThinkingEvent,
  VehicleStateUpdate,
} from "@/types";

export function useSocket(): void {
  const sessionId = useAppStore((state) => state.sessionId);
  const isSessionReady = useAppStore((state) => state.isSessionReady);
  const setConnected = useAppStore((state) => state.setConnected);
  const addMessage = useChatStore((state) => state.addMessage);
  const setThinkingStep = useChatStore((state) => state.setThinkingStep);
  const setProcessing = useChatStore((state) => state.setProcessing);
  const setError = useChatStore((state) => state.setError);
  const setVehicle = useVehicleStore((state) => state.setVehicle);

  useEffect(() => {
    if (!sessionId || !isSessionReady) return;

    const handleConnect = () => {
      setConnected(true);
      setError(null);
    };
    const handleDisconnect = () => setConnected(false);
    const handleConnectError = () => {
      setConnected(false);
      setProcessing(false);
      setError("无法连接到 Agent 服务，请确认后端已启动。");
    };
    const handleThinking = (event: AgentThinkingEvent) => {
      if (event.session_id !== sessionId) return;
      setProcessing(true);
      setThinkingStep(event.step);
    };
    const handleResponse = (response: AgentResponse) => {
      if (response.session_id !== sessionId) return;
      addMessage({
        role: "assistant",
        content: response.user_response,
        timestamp: response.timestamp,
        agentResponse: response,
      });
      setThinkingStep(null);
      setProcessing(false);
      setError(null);
    };
    const handleVehicleUpdate = (event: VehicleStateUpdate) => {
      if (event.session_id === sessionId) setVehicle(event.vehicle);
    };
    const handleAgentError = (event: AgentErrorEvent) => {
      if (event.session_id && event.session_id !== sessionId) return;
      setThinkingStep(null);
      setProcessing(false);
      setError(event.message);
    };

    socket.on("connect", handleConnect);
    socket.on("disconnect", handleDisconnect);
    socket.on("connect_error", handleConnectError);
    socket.on("agent_thinking", handleThinking);
    socket.on("agent_response", handleResponse);
    socket.on("vehicle_state_update", handleVehicleUpdate);
    socket.on("agent_error", handleAgentError);

    if (socket.connected) handleConnect();
    else socket.connect();

    return () => {
      socket.off("connect", handleConnect);
      socket.off("disconnect", handleDisconnect);
      socket.off("connect_error", handleConnectError);
      socket.off("agent_thinking", handleThinking);
      socket.off("agent_response", handleResponse);
      socket.off("vehicle_state_update", handleVehicleUpdate);
      socket.off("agent_error", handleAgentError);
      socket.disconnect();
      setConnected(false);
    };
  }, [
    addMessage,
    isSessionReady,
    sessionId,
    setConnected,
    setError,
    setProcessing,
    setThinkingStep,
    setVehicle,
  ]);
}
