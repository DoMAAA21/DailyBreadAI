"use client";

import { useState } from "react";
import { BookOpen, Search } from "lucide-react";
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
    <div className="flex min-h-full items-center justify-center bg-background p-4 sm:p-6">
      <div className="flex h-[min(720px,calc(100vh-3rem))] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-sacred-gold/20 bg-aged-parchment shadow-2xl">
        <header className="flex items-center gap-3 bg-primary px-5 py-4">
          <div className="flex size-10 items-center justify-center rounded-lg bg-sacred-gold/20">
            <BookOpen className="size-5 text-sacred-gold" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-primary-foreground">Rhema</h1>
            <p className="text-sm text-primary-foreground/80">
              Search the Word with AI
            </p>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex flex-col gap-3",
                  message.role === "user" ? "items-end" : "items-start"
                )}
              >
                {message.role === "user" ? (
                  <div className="max-w-[85%] rounded-2xl rounded-br-md bg-monastery-brown px-4 py-3 text-sm leading-relaxed text-aged-parchment">
                    {message.content}
                  </div>
                ) : (
                  <div className="w-full space-y-3">
                    <div className="max-w-[95%] text-sm leading-relaxed text-black">
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
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-3 border-t border-sacred-gold/20 bg-aged-parchment px-5 py-4"
          >
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="What does the Bible say about peace?"
              className="h-11 border-deep-parchment/20 bg-white text-black placeholder:text-muted-foreground"
            />
            <Button
              type="submit"
              className="h-11 w-full bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Search className="size-4" />
              Search Scripture
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
