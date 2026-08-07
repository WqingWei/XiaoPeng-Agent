const SESSION_STORAGE_KEY = "xiaopeng-agent-session-id";

export function createSessionId(): string {
  const suffix =
    typeof globalThis.crypto?.randomUUID === "function"
      ? globalThis.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `xpeng-${suffix}`;
}

export function getOrCreateSessionId(storage: Storage): string {
  const existing = storage.getItem(SESSION_STORAGE_KEY)?.trim();
  if (existing) return existing;

  const sessionId = createSessionId();
  storage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

export { SESSION_STORAGE_KEY };
