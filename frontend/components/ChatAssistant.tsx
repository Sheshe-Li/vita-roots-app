"use client";

import { useState, useRef, useEffect } from "react";
import {
  MessageCircle,
  X,
  Send,
  Loader2,
  User,
  Bot,
  ChevronDown,
} from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

interface FamilyMember {
  id: string;
  name: string;
}

interface Family {
  id: string;
  name: string;
  members: FamilyMember[];
}

interface Props {
  familyId: string;
  family: Family | null;
  selectedMemberId: string | null;
}

const SUGGESTED_PROMPTS = [
  "What's a quick dinner idea for tonight?",
  "How can we reduce our grocery budget?",
  "Which supplements are best for energy?",
  "Any healthy snack ideas for kids?",
];

export default function ChatAssistant({ familyId, family, selectedMemberId }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your family wellness assistant. I can help with meal ideas, grocery tips, supplement guidance, and more. What would you like to explore today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeMemberId, setActiveMemberId] = useState<string | null>(
    selectedMemberId
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setActiveMemberId(selectedMemberId);
  }, [selectedMemberId]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const sendMessage = async (messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || isStreaming) return;

    setInput("");
    const userMessage: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);

    // Add streaming placeholder
    const assistantPlaceholder: ChatMessage = {
      role: "assistant",
      content: "",
      streaming: true,
    };
    setMessages((prev) => [...prev, assistantPlaceholder]);
    setIsStreaming(true);

    try {
      const history = messages
        .filter((m) => !m.streaming)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_id: familyId,
          message: text,
          conversation_history: history,
          member_id: activeMemberId,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to connect to assistant.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                fullContent += data.chunk;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  updated[lastIdx] = {
                    ...updated[lastIdx],
                    content: fullContent,
                    streaming: !data.done,
                  };
                  return updated;
                });
              }
              if (data.done) break;
            } catch {
              // Skip malformed SSE lines
            }
          }
        }
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        updated[lastIdx] = {
          role: "assistant",
          content: `Sorry, I ran into an issue: ${errMsg} Please try again.`,
          streaming: false,
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const activeMember = family?.members.find((m) => m.id === activeMemberId);

  return (
    <>
      {/* Floating bubble */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-brand-600 hover:bg-brand-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center z-50 group"
          aria-label="Open wellness assistant"
        >
          <MessageCircle className="w-6 h-6" />
          <span className="absolute -top-10 right-0 bg-stone-800 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Wellness Assistant
          </span>
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[400px] max-h-[80vh] bg-white rounded-2xl shadow-2xl border border-stone-100 flex flex-col z-50 animate-slide-up overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-brand-600 to-brand-700 text-white">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="font-semibold text-sm">Wellness Assistant</p>
                <p className="text-brand-200 text-xs">
                  {family?.name
                    ? `Helping the ${family.name} family`
                    : "Family Wellness AI"}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Member selector */}
          {family && family.members.length > 0 && (
            <div className="px-4 py-2.5 border-b border-stone-100 flex items-center gap-2">
              <span className="text-xs text-stone-400 font-medium flex-shrink-0">
                Asking for:
              </span>
              <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
                <button
                  onClick={() => setActiveMemberId(null)}
                  className={`flex-shrink-0 text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                    !activeMemberId
                      ? "bg-brand-100 text-brand-700"
                      : "bg-stone-100 text-stone-500 hover:bg-stone-200"
                  }`}
                >
                  Whole family
                </button>
                {family.members.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setActiveMemberId(m.id)}
                    className={`flex-shrink-0 text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                      activeMemberId === m.id
                        ? "bg-brand-100 text-brand-700"
                        : "bg-stone-100 text-stone-500 hover:bg-stone-200"
                    }`}
                  >
                    {m.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex items-start gap-2.5 ${
                  msg.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    msg.role === "user"
                      ? "bg-brand-600 text-white"
                      : "bg-stone-100 text-stone-600"
                  }`}
                >
                  {msg.role === "user" ? (
                    <User className="w-3.5 h-3.5" />
                  ) : (
                    <Bot className="w-3.5 h-3.5" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-brand-600 text-white rounded-tr-sm"
                      : "bg-stone-100 text-stone-800 rounded-tl-sm"
                  }`}
                >
                  {msg.content}
                  {msg.streaming && (
                    <span className="inline-flex items-center ml-1 gap-0.5">
                      <span className="w-1 h-1 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1 h-1 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1 h-1 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested prompts (shown when only greeting) */}
          {messages.length === 1 && (
            <div className="px-4 pb-2">
              <p className="text-xs text-stone-400 mb-2">Try asking:</p>
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    className="text-xs bg-brand-50 text-brand-700 px-2.5 py-1.5 rounded-lg hover:bg-brand-100 transition-colors border border-brand-100"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-stone-100">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Ask about ${activeMember?.name || "your family"}'s wellness...`}
                rows={1}
                className="flex-1 input-field resize-none py-2.5 text-sm leading-relaxed max-h-24"
                style={{ minHeight: "42px" }}
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isStreaming}
                className="flex-shrink-0 w-10 h-10 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-colors"
              >
                {isStreaming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-stone-300 mt-2 text-center">
              Informational only — not medical advice
            </p>
          </div>
        </div>
      )}
    </>
  );
}
