/**
 * Chat Input Component
 *
 * LEARNING MODULE 6: AI CHAT WITH VERCEL AI SDK
 * ----------------------------------------------
 * This component handles user input for the chat.
 *
 * Key concepts:
 * 1. **Form handling** - Submit on Enter or button click
 * 2. **Controlled input** - React manages the input value
 * 3. **Loading states** - Disable during AI response
 *
 * File path: frontend/components/chat/ChatInput.tsx
 */

"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ChatInputProps {
  /** Current input value */
  input: string;
  /** Callback when input changes */
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Callback when form is submitted */
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  /** Whether the AI is currently responding */
  isLoading: boolean;
}

/**
 * Chat input form with send button
 *
 * LEARNING NOTE:
 * This component receives all state and handlers from the parent.
 * This pattern (controlled component) makes it easy to:
 * - Clear input after sending
 * - Validate before sending
 * - Share state with other components
 */
export function ChatInput({
  input,
  onInputChange,
  onSubmit,
  isLoading,
}: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="flex gap-2">
      <Input
        value={input}
        onChange={onInputChange}
        placeholder="Ask about trading signals, indicators, or analysis..."
        disabled={isLoading}
        className="flex-1"
      />
      <Button type="submit" disabled={isLoading || !input?.trim()}>
        {isLoading ? (
          // Loading spinner
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
        ) : (
          // Send icon
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        )}
      </Button>
    </form>
  );
}
