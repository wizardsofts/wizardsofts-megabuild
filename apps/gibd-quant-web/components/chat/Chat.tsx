/**
 * Chat Component (Main Chat Interface)
 *
 * LEARNING MODULE 6: AI CHAT WITH VERCEL AI SDK
 * ----------------------------------------------
 * This is the main chat interface that combines all chat functionality.
 *
 * Key concepts:
 * 1. **useChat hook** - Manages chat state, streaming, and API calls
 * 2. **Auto-scroll** - Scroll to bottom when new messages arrive
 * 3. **Streaming UI** - Show response as it's generated
 *
 * The useChat hook provides:
 * - messages: Array of all messages
 * - input: Current input text
 * - handleInputChange: Handler for input changes
 * - handleSubmit: Handler for form submission
 * - isLoading: Whether AI is responding
 * - error: Any error that occurred
 *
 * File path: frontend/components/chat/Chat.tsx
 */

"use client";

import { useChat } from "@ai-sdk/react";
import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Main chat interface component
 *
 * LEARNING NOTE:
 * The useChat hook from Vercel AI SDK handles:
 * 1. State management for messages
 * 2. API calls to /api/chat
 * 3. Streaming response handling
 * 4. Error handling
 *
 * You just need to provide the UI!
 */
export function Chat() {
  /**
   * useChat hook - the magic of Vercel AI SDK
   *
   * LEARNING NOTE:
   * This single hook handles everything:
   * - Sends messages to /api/chat (configurable via `api` option)
   * - Parses streaming responses
   * - Updates messages array in real-time
   * - Manages loading state
   */
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
  } = useChat({
    // API endpoint (defaults to /api/chat)
    api: "/api/chat",
  });

  /**
   * Auto-scroll to bottom when new messages arrive
   *
   * LEARNING NOTE:
   * We use a ref to access the DOM element directly.
   * useEffect runs after render, so the new message
   * is already in the DOM when we scroll.
   */
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Default suggested questions - mix of queries and explanations
  const questions = [
    "Analyze GP",
    "Show all bank stocks",
    "Top 10 stocks by volume",
    "Stocks with RSI above 70",
  ];

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-blue-600"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
              clipRule="evenodd"
            />
          </svg>
          AI Trading Assistant
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-hidden">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
          {/**
           * Welcome Message - shown when no messages yet
           *
           * LEARNING NOTE:
           * We show a static welcome message instead of using initialMessages
           * to avoid potential hydration issues with the AI SDK.
           */}
          {messages.length === 0 && (
            <>
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
                  <div className="text-xs font-medium mb-1 text-gray-500">
                    Assistant
                  </div>
                  <div className="text-sm whitespace-pre-wrap">
                    Hello! I&apos;m your DSE stock assistant. You can ask me about stocks, signals, and indicators. Try queries like &quot;show all bank stocks&quot; or &quot;top 10 by volume&quot;.
                  </div>
                </div>
              </div>

              {/* Suggested Questions - displayed as hints */}
              <div className="flex flex-wrap gap-2 mt-2">
                {questions.map((question, index) => (
                  <span
                    key={index}
                    className="text-sm bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full"
                  >
                    {question}
                  </span>
                ))}
              </div>
            </>
          )}

          {/* Actual chat messages */}
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {/* Loading indicator while AI is responding */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Thinking...
                </div>
              </div>
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
              Error: {error.message}
            </div>
          )}

          {/* Invisible element for auto-scroll */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <ChatInput
          input={input}
          onInputChange={handleInputChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </CardContent>
    </Card>
  );
}
