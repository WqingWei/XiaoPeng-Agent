"use client";

import { ArrowUp, LoaderCircle } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks";
import { useAppStore, useChatStore } from "@/stores";

export function ChatInput() {
  const [text, setText] = useState("");
  const isProcessing = useChatStore((state) => state.isProcessing);
  const isSessionReady = useAppStore((state) => state.isSessionReady);
  const { sendMessage } = useChat();

  function submit() {
    if (sendMessage(text)) setText("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isProcessing) submit();
    }
  }

  return (
    <form
      className="flex items-end gap-2 rounded-2xl border border-white/10 bg-card p-2 focus-within:border-xpeng-green/40"
      onSubmit={handleSubmit}
    >
      <textarea
        aria-label="发送消息"
        className="max-h-32 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-5 outline-none placeholder:text-muted-foreground/70 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isProcessing || !isSessionReady}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          isSessionReady ? "告诉我您需要什么出行服务..." : "正在恢复会话历史..."
        }
        rows={1}
        value={text}
      />
      <Button
        aria-label="发送"
        className="size-9 rounded-xl"
        disabled={isProcessing || !isSessionReady || !text.trim()}
        size="icon-lg"
        type="submit"
      >
        {isProcessing ? <LoaderCircle className="animate-spin" /> : <ArrowUp />}
      </Button>
    </form>
  );
}
