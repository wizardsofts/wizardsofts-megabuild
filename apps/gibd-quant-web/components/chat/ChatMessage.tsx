/**
 * Chat Message Component
 *
 * LEARNING MODULE 6: AI CHAT WITH VERCEL AI SDK
 * ----------------------------------------------
 * This component renders individual chat messages with markdown support.
 *
 * Key concepts:
 * 1. **Message types** - User vs Assistant messages
 * 2. **Conditional styling** - Different styles per role
 * 3. **Markdown rendering** - Tables, bold, lists from AI responses
 *
 * File path: frontend/components/chat/ChatMessage.tsx
 */

"use client";

import { cn } from "@/lib/utils";
import type { Message } from "@ai-sdk/react";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  /** The message to display */
  message: Message;
}

/**
 * Renders a single chat message with appropriate styling
 *
 * LEARNING NOTE:
 * The Message type from 'ai' package has:
 * - id: unique identifier
 * - role: 'user' | 'assistant' | 'system'
 * - content: the message text
 * - createdAt: timestamp (optional)
 */
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[90%] rounded-lg px-4 py-2",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        )}
      >
        {/* Role indicator */}
        <div
          className={cn(
            "text-xs font-medium mb-1",
            isUser ? "text-blue-200" : "text-gray-500"
          )}
        >
          {isUser ? "You" : "Assistant"}
        </div>

        {/* Message content with markdown rendering */}
        <div className="text-sm prose prose-sm max-w-none prose-p:my-1 prose-table:my-2">
          {isUser ? (
            // Plain text for user messages
            <span className="whitespace-pre-wrap">{message.content}</span>
          ) : (
            // Markdown for assistant messages
            <ReactMarkdown
              components={{
                // Style tables for stock data
                table: ({ children }) => (
                  <table className="min-w-full text-xs border-collapse my-2">
                    {children}
                  </table>
                ),
                thead: ({ children }) => (
                  <thead className="bg-gray-200">{children}</thead>
                ),
                th: ({ children }) => (
                  <th className="px-2 py-1 text-left font-semibold border-b">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-2 py-1 border-b border-gray-200">
                    {children}
                  </td>
                ),
                // Style bold text
                strong: ({ children }) => (
                  <strong className="font-semibold text-gray-900">
                    {children}
                  </strong>
                ),
                // Style lists
                ul: ({ children }) => (
                  <ul className="list-disc list-inside my-1 space-y-0.5">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="text-gray-700">{children}</li>
                ),
                // Style paragraphs
                p: ({ children }) => (
                  <p className="my-1">{children}</p>
                ),
                // Style emphasis (italic)
                em: ({ children }) => (
                  <em className="text-gray-600 text-xs">{children}</em>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}
