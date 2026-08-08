import assert from "node:assert/strict";
import test from "node:test";

import { createSessionId, getOrCreateSessionId } from "../src/lib/session.ts";
import { getScenarioInputPrompt } from "../src/lib/scenarios.ts";
import { useChatStore } from "../src/stores/chatStore.ts";
import type { AgentResponse } from "../src/types/agent.ts";

class MemoryStorage implements Storage {
  private values = new Map<string, string>();

  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  key(index: number): string | null {
    return [...this.values.keys()][index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

test("同一标签页刷新复用 session ID，不同标签页使用独立 ID", () => {
  const firstTab = new MemoryStorage();
  const secondTab = new MemoryStorage();

  const firstId = getOrCreateSessionId(firstTab);

  assert.equal(getOrCreateSessionId(firstTab), firstId);
  assert.notEqual(getOrCreateSessionId(secondTab), firstId);
  assert.match(firstId, /^xpeng-/);
  assert.match(createSessionId(), /^xpeng-/);
});

test("历史水合恢复消息和最后一轮决策详情", () => {
  const response = {
    session_id: "session-a",
    turn_id: 1,
    user_response: "已打开空调",
  } as AgentResponse;

  useChatStore.getState().hydrateMessages([
    {
      role: "user",
      content: "打开空调",
      timestamp: "2026-08-07T10:00:00Z",
    },
    {
      role: "assistant",
      content: "已打开空调",
      timestamp: "2026-08-07T10:00:01Z",
      agent_response: response,
    },
  ]);

  const state = useChatStore.getState();
  assert.deepEqual(
    state.messages.map((message) => [message.role, message.content]),
    [
      ["user", "打开空调"],
      ["assistant", "已打开空调"],
    ],
  );
  assert.equal(state.selectedResponse?.turn_id, 1);
});

test("场景或模式切换响应水合时保留已有对话并隐藏系统提示", () => {
  useChatStore.getState().hydrateMessages([
    {
      role: "user",
      content: "这是切换前的消息",
      timestamp: "2026-08-07T10:00:00Z",
    },
    {
      role: "assistant",
      content: "这是切换前的回复",
      timestamp: "2026-08-07T10:00:01Z",
    },
    {
      role: "system",
      content: "已切换至新场景。",
      timestamp: "2026-08-07T10:00:02Z",
    },
  ]);

  assert.deepEqual(
    useChatStore.getState().messages.map((message) => message.content),
    ["这是切换前的消息", "这是切换前的回复"],
  );
});

test("不同场景返回对应的输入框提示", () => {
  assert.match(getScenarioInputPrompt("fatigue_driving"), /疲劳信号/);
  assert.match(getScenarioInputPrompt("change_destination"), /新的目的地/);
  assert.match(getScenarioInputPrompt("passenger_help"), /紧急程度/);
  assert.equal(getScenarioInputPrompt(null), "告诉我您需要什么出行服务…");
});
