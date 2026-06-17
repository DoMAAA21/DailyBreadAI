"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerseCard } from "@/app/(home)/_components/verse-card";
import { cn } from "@/lib/utils";
import { http } from "@/utils/http";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  verse?: {
    text: string;
    reference: string;
  };
};

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const { data } = await http.post<{ reply: string }>("/chat", {
        message: question,
      });

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Sorry, I could not reach the server. Make sure the API and Ollama are running.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain px-5 py-5 sm:px-8">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ask a question about Scripture to get started.
          </p>
        ) : null}
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
                <div className="rounded-2xl rounded-bl-md border border-sacred-gold/20 bg-white px-4 py-3 text-sm leading-relaxed text-black shadow-sm">
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
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Thinking...
          </div>
        ) : null}
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
          disabled={isLoading}
          className="h-11 border-deep-parchment/20 bg-white text-black placeholder:text-muted-foreground"
        />
        <Button
          type="submit"
          disabled={isLoading}
          className="h-11 w-full bg-primary text-primary-foreground hover:bg-primary/90 sm:w-auto sm:min-w-48"
        >
          {isLoading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Search className="size-4" />
          )}
          Search Scripture
        </Button>
      </form>
    </div>
  );
}
