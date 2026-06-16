"use client";

import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerseCard } from "@/app/(home)/_components/verse-card";
import { cn } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  verse?: {
    text: string;
    reference: string;
  };
};

const MOCK_MESSAGES: Message[] = [
  {
    id: "1",
    role: "user",
    content: "What does the Bible say about peace?",
  },
  {
    id: "2",
    role: "assistant",
    content:
      "Scripture speaks of a peace that comes from God — not as the world gives, but a lasting peace rooted in Christ.",
    verse: {
      text: "Peace I leave with you; my peace I give you. I do not give to you as the world gives.",
      reference: "John 14:27 (NIV)",
    },
  },
];

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");

    // Placeholder assistant reply until API is wired up
    setTimeout(() => {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Here is what Scripture says on that topic. Connect the API to get live answers from your RAG pipeline.",
          verse: {
            text: "Be still, and know that I am God.",
            reference: "Psalm 46:10 (NIV)",
          },
        },
      ]);
    }, 600);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain px-5 py-5 sm:px-8">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex flex-col gap-3",
              message.role === "user" ? "items-end" : "items-start"
            )}
          >
            {message.role === "user" ? (
              <div className="max-w-[85%] rounded-2xl rounded-br-md bg-monastery-brown px-4 py-3 text-sm leading-relaxed text-aged-parchment sm:max-w-xl">
                {message.content}
              </div>
            ) : (
              <div className="w-full max-w-3xl space-y-3">
                <div className="text-sm leading-relaxed text-black">
                  {message.content}
                </div>
                {message.verse ? (
                  <VerseCard
                    text={message.verse.text}
                    reference={message.verse.reference}
                  />
                ) : null}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="shrink-0 space-y-3 border-t border-sacred-gold/20 bg-background px-5 py-4 sm:px-8 flex space-x-2"
      >
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="What does the Bible say about peace?"
          className="h-11 border-deep-parchment/20 bg-white text-black placeholder:text-muted-foreground"
        />
        <Button
          type="submit"
          className="h-11 w-full bg-primary text-primary-foreground hover:bg-primary/90 sm:w-auto sm:min-w-48"
        >
          <Search className="size-4" />
          Search Scripture
        </Button>
      </form>
    </div>
  );
}
