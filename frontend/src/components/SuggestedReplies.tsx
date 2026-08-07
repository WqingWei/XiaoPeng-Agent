"use client";

import { CornerDownLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks";

export function SuggestedReplies({ replies, disabled = false }: { replies: string[]; disabled?: boolean }) {
  const { sendMessage } = useChat();
  if (!replies.length) return null;

  return (
    <div className="flex flex-wrap gap-2" aria-label="建议回复">
      {replies.map((reply) => (
        <Button
          key={reply}
          className="rounded-full border-xpeng-green/25 bg-xpeng-green/5 text-xs text-xpeng-green hover:bg-xpeng-green/10"
          disabled={disabled}
          onClick={() => sendMessage(reply)}
          size="sm"
          variant="outline"
        >
          {reply}
          <CornerDownLeft className="size-3" />
        </Button>
      ))}
    </div>
  );
}
