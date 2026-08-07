"use client";

import { Bot, CircleUserRound, Info, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { Button } from "@/components/ui/button";
import { useChatStore, type ChatMessage } from "@/stores";

function formatTime(timestamp: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(timestamp));
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const setSelectedResponse = useChatStore((state) => state.setSelectedResponse);

  if (message.role === "system") {
    return (
      <div className="flex justify-center py-1">
        <div className="inline-flex max-w-[90%] items-center gap-2 rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-center text-[11px] text-muted-foreground">
          <Info className="size-3 shrink-0 text-xpeng-green" />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";
  const Icon = isUser ? CircleUserRound : Bot;
  return (
    <article className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`mt-1 grid size-7 shrink-0 place-items-center rounded-lg ${isUser ? "bg-xpeng-green text-primary-foreground" : "bg-white/8 text-xpeng-green"}`}>
        <Icon className="size-4" aria-hidden="true" />
      </div>
      <div className={`min-w-0 max-w-[82%] ${isUser ? "items-end" : "items-start"}`}>
        <div className={`rounded-2xl px-3.5 py-2.5 text-sm leading-6 ${isUser ? "rounded-tr-sm bg-xpeng-green text-primary-foreground" : "rounded-tl-sm border border-white/10 bg-card"}`}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
                ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
                code: ({ children }) => <code className="rounded bg-black/30 px-1 py-0.5 font-mono text-xs text-xpeng-green">{children}</code>,
                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        <div className={`mt-1 flex items-center gap-2 px-1 ${isUser ? "justify-end" : "justify-start"}`}>
          <time className="text-[10px] text-muted-foreground" dateTime={message.timestamp}>
            {formatTime(message.timestamp)}
          </time>
          {message.agentResponse ? (
            <Button
              className="h-auto gap-1 px-0 py-0 text-[10px] text-muted-foreground hover:bg-transparent hover:text-xpeng-green"
              onClick={() => {
                setSelectedResponse(message.agentResponse ?? null);
                document.getElementById("agent-panel")?.scrollIntoView({ behavior: "smooth" });
              }}
              size="xs"
              variant="ghost"
            >
              <Sparkles className="size-3" />
              查看详情
            </Button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
