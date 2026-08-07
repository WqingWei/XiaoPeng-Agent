"use client";

import { MessageSquareText } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";

import { ChatInput } from "@/components/ChatInput";
import { LoadingDots } from "@/components/LoadingDots";
import { MessageBubble } from "@/components/MessageBubble";
import { SuggestedReplies } from "@/components/SuggestedReplies";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStore } from "@/stores";

export function ChatPanel() {
  const messages = useChatStore((state) => state.messages);
  const thinkingStep = useChatStore((state) => state.thinkingStep);
  const isProcessing = useChatStore((state) => state.isProcessing);
  const error = useChatStore((state) => state.error);
  const sceneTransition = useChatStore((state) => state.sceneTransition);
  const endRef = useRef<HTMLDivElement>(null);
  const suggestedReplies = useMemo(
    () =>
      [...messages]
        .reverse()
        .find((message) => message.agentResponse)
        ?.agentResponse?.follow_up.suggested_replies ?? [],
    [messages],
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, isProcessing]);

  return (
    <section className="flex min-h-[560px] min-w-0 flex-col bg-background lg:min-h-0">
      <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.2em] text-xpeng-green">CONVERSATION</p>
          <h2 className="mt-1 text-base font-semibold">对话交互</h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] text-muted-foreground">
          {messages.length} 条消息
        </span>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div
          aria-busy={sceneTransition !== "idle"}
          className="scene-content mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-5 sm:px-6"
          data-transition={sceneTransition}
        >
          {messages.length ? (
            messages.map((message) => <MessageBubble key={message.id} message={message} />)
          ) : (
            <div className="grid min-h-72 place-items-center text-center">
              <div>
                <span className="mx-auto grid size-12 place-items-center rounded-2xl border border-xpeng-green/20 bg-xpeng-green/5 text-xpeng-green">
                  <MessageSquareText className="size-6" />
                </span>
                <p className="mt-4 text-sm font-medium">准备好规划您的出行服务</p>
                <p className="mt-1 text-xs text-muted-foreground">选择左侧场景，或直接输入您的需求</p>
              </div>
            </div>
          )}
          {isProcessing ? <LoadingDots step={thinkingStep} /> : null}
          <div ref={endRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-white/8 bg-background/95 px-4 py-3 sm:px-5">
        <div className="mx-auto max-w-3xl space-y-2.5">
          {error ? (
            <p className="rounded-lg border border-red-500/20 bg-red-500/8 px-3 py-2 text-xs text-red-300" role="alert">
              {error}
            </p>
          ) : null}
          <SuggestedReplies disabled={isProcessing} replies={suggestedReplies} />
          <ChatInput />
          <p className="text-center text-[10px] text-muted-foreground/70">Enter 发送 · Shift + Enter 换行</p>
        </div>
      </div>
    </section>
  );
}
