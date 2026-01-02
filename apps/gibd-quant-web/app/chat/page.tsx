/**
 * AI Chat Page
 *
 * LEARNING MODULE 6: AI CHAT WITH VERCEL AI SDK
 * ----------------------------------------------
 * This page provides an AI-powered chat interface for users
 * to ask questions about trading signals and analysis.
 *
 * Architecture:
 * 1. This page is a Server Component (no "use client")
 * 2. It renders the Chat component (Client Component)
 * 3. Chat component uses useChat hook for AI interaction
 * 4. API route /api/chat handles AI requests
 *
 * File path: frontend/app/chat/page.tsx
 * See: frontend/LEARNING.md#module-6-ai-chat
 */

import { Chat } from "@/components/chat";
import Link from "next/link";

export default function ChatPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <nav className="text-sm text-gray-500 mb-2">
          <Link href="/" className="hover:text-gray-700">
            Home
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">AI Chat</span>
        </nav>
        <h1 className="text-3xl font-bold text-gray-900">DSE Stock Assistant</h1>
        <p className="text-gray-600 mt-1">
          Query stocks using natural language - try &quot;show all bank stocks&quot; or &quot;top 10 by volume&quot;
        </p>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <Chat />
        </div>

        {/* Sidebar - Suggested Questions */}
        <div className="space-y-6">
          {/* Quick Questions Card */}
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              Suggested Questions
            </h2>
            <div className="space-y-2">
              {[
                "Show all bank stocks",
                "Top 10 stocks by volume",
                "Stocks with RSI above 70",
                "Overbought stocks",
                "What does RSI tell us?",
              ].map((question, index) => (
                <button
                  key={index}
                  className="w-full text-left text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Info Card */}
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              About the Assistant
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Query DSE stocks using natural language:
            </p>
            <ul className="text-sm text-gray-600 space-y-2">
              <li className="flex items-start gap-2">
                <svg className="h-5 w-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Sector queries (bank, pharma, telecom)
              </li>
              <li className="flex items-start gap-2">
                <svg className="h-5 w-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Indicator filters (RSI above 70)
              </li>
              <li className="flex items-start gap-2">
                <svg className="h-5 w-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Rankings (top 10 by volume)
              </li>
              <li className="flex items-start gap-2">
                <svg className="h-5 w-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Indicator explanations
              </li>
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex gap-2">
              <svg className="h-5 w-5 text-amber-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <p className="text-xs text-amber-800">
                <strong>Disclaimer:</strong> This assistant provides educational information only.
                Trading signals and AI responses are not financial advice. Always do your own
                research before making investment decisions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Learning callout */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          Module 6: AI Chat with Vercel AI SDK
        </h3>
        <p className="text-blue-800 text-sm">
          This page demonstrates streaming AI chat integration. Key learnings:
        </p>
        <ul className="text-blue-800 text-sm mt-2 space-y-1 list-disc list-inside">
          <li>useChat hook manages chat state and streaming</li>
          <li>API route at /api/chat handles AI requests</li>
          <li>Edge Runtime for fast streaming responses</li>
          <li>System prompts give AI domain context</li>
        </ul>
        <p className="text-blue-700 text-sm mt-2">
          See <code className="bg-blue-100 px-1 rounded">frontend/LEARNING.md#module-6-ai-chat</code> for details.
        </p>
      </div>
    </div>
  );
}
