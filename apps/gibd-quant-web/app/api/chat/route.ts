/**
 * Chat API Route Handler
 *
 * LEARNING MODULE 6: AI CHAT WITH VERCEL AI SDK
 * ----------------------------------------------
 * This module teaches you how to build a stock query chat in Next.js.
 *
 * Key concepts:
 * 1. **API Routes** - Server-side endpoints in Next.js
 * 2. **NLQ Integration** - Natural language queries to backend
 * 3. **Hybrid responses** - Stock data + AI explanations
 *
 * File path: frontend/app/api/chat/route.ts
 * See: frontend/LEARNING.md#module-6-ai-chat
 */

import { streamText } from "ai";
import { createOpenAI } from "@ai-sdk/openai";

/**
 * Use Edge Runtime for faster cold starts and streaming
 */
export const runtime = "edge";

/**
 * Backend API URL from environment
 */
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

/**
 * Create OpenAI-compatible client for general AI responses
 */
const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY || "dummy-key-for-ollama",
  baseURL: process.env.OPENAI_BASE_URL || "https://api.openai.com/v1",
});

/**
 * System prompt for DSE stock assistant
 */
const SYSTEM_PROMPT = `You are a helpful DSE (Dhaka Stock Exchange) stock assistant for Guardian Investment BD.

You help users with:
- Stock queries (use NLQ system for data)
- Technical indicators (RSI, MACD, SMA, ADX, ATR)
- Signal explanations (BUY, SELL, HOLD)
- Sector analysis

Key information:
- Signals: BUY (score >= 0.4), SELL (score <= -0.4), HOLD (in between)
- Confidence: 0 to 1 (higher = more reliable)
- Total score: -1 to +1 (positive = bullish, negative = bearish)

When users ask about stocks, you will receive data from the NLQ system. Format responses clearly with the data provided.

Example queries users might ask:
- "show all bank stocks"
- "stocks with RSI above 70"
- "top 10 by volume"
- "what is BATBC's signal?"

Always remind users that signals are for informational purposes only, not financial advice.`;

/**
 * Patterns that indicate a stock data query vs general question
 */
const STOCK_QUERY_PATTERNS = [
  /show\s+(all|me)?\s*(\w+)?\s*stocks?/i,
  /list\s+(\w+)?\s*stocks?/i,
  /stocks?\s+with\s+/i,
  /top\s+\d+/i,
  /highest|lowest/i,
  /rsi\s+(above|below|over|under)/i,
  /volume\s+(above|below)/i,
  /increasing|decreasing/i,
  /overbought|oversold/i,
  /outperforming|underperforming/i,
  /sector\s+stocks/i,
  /bank\s+stocks|pharma\s+stocks|telecom\s+stocks/i,
];

/**
 * Patterns that indicate a single stock analysis query
 * Returns the ticker symbol if matched
 */
const ANALYZE_PATTERNS = [
  /^analyze\s+([A-Z0-9]+)$/i,                           // "analyze GP"
  /^analyze\s+([A-Z0-9]+)\s+stock$/i,                   // "analyze GP stock"
  /^signal\s+for\s+([A-Z0-9]+)$/i,                      // "signal for GP"
  /^what(?:'s|\s+is)\s+([A-Z0-9]+)(?:'s)?\s+signal\??$/i,  // "what is GP's signal?" or "what's GP signal"
  /^([A-Z0-9]+)\s+signal\??$/i,                         // "GP signal?"
  /^([A-Z0-9]+)\s+analysis$/i,                          // "GP analysis"
  /^give\s+me\s+(?:analysis|signal)\s+(?:for\s+)?([A-Z0-9]+)$/i,  // "give me analysis for GP"
  /^how\s+is\s+([A-Z0-9]+)\s+(?:doing|looking)\??$/i,   // "how is GP doing?"
];

/**
 * Check if a message is a stock data query
 */
function isStockQuery(message: string): boolean {
  return STOCK_QUERY_PATTERNS.some((pattern) => pattern.test(message));
}

/**
 * Check if a message is a single stock analysis query
 * Returns the ticker symbol if matched, null otherwise
 */
function extractAnalyzeTicker(message: string): string | null {
  const trimmed = message.trim();
  for (const pattern of ANALYZE_PATTERNS) {
    const match = trimmed.match(pattern);
    if (match && match[1]) {
      return match[1].toUpperCase();
    }
  }
  return null;
}

/**
 * Call the backend NLQ endpoint
 */
async function executeNLQQuery(
  query: string
): Promise<{ success: boolean; data?: NLQResponse; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/nlq/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 20 }),
    });

    if (!response.ok) {
      return { success: false, error: `Backend error: ${response.status}` };
    }

    const data = await response.json();
    return { success: data.success, data, error: data.error };
  } catch (error) {
    console.error("NLQ query error:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Backend unavailable",
    };
  }
}

interface NLQResponse {
  success: boolean;
  query_type: string | null;
  interpretation: string | null;
  results: Array<Record<string, unknown>>;
  count: number;
  error: string | null;
}

interface AnalyzeResponse {
  success: boolean;
  ticker: string;
  sector: string | null;
  signal_date: string;
  signal: {
    type: string;
    confidence: number;
    total_score: number;
  };
  prices: {
    entry: number;
    target: number;
    stop_loss: number;
    risk_reward: number;
  };
  hold_period: {
    min_days: number;
    max_days: number;
  };
  trailing_stop: number;
  scores: Record<string, number>;
  weights: Record<string, number>;
  warnings: string[];
}

/**
 * Call the backend analyze endpoint for single stock analysis
 */
async function executeAnalyzeQuery(
  ticker: string
): Promise<{ success: boolean; data?: AnalyzeResponse; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/analyze/${ticker}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || `Backend error: ${response.status}`,
      };
    }

    const data = await response.json();
    return { success: data.success, data, error: undefined };
  } catch (error) {
    console.error("Analyze query error:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Backend unavailable",
    };
  }
}

/**
 * Format analyze results as a readable response
 */
function formatAnalyzeResponse(data: AnalyzeResponse): string {
  const signalEmoji =
    data.signal.type === "BUY"
      ? "🟢"
      : data.signal.type === "SELL"
        ? "🔴"
        : "🟡";

  let response = `## ${signalEmoji} ${data.ticker} Analysis\n\n`;

  // Basic info
  if (data.sector) {
    response += `**Sector:** ${data.sector}\n`;
  }
  response += `**Date:** ${data.signal_date}\n\n`;

  // Signal summary
  response += `### Signal: ${data.signal.type}\n`;
  response += `| Metric | Value |\n`;
  response += `|--------|-------|\n`;
  response += `| Confidence | ${(data.signal.confidence * 100).toFixed(0)}% |\n`;
  response += `| Total Score | ${data.signal.total_score.toFixed(3)} |\n\n`;

  // Price targets
  response += `### Price Targets\n`;
  response += `| | Price (৳) |\n`;
  response += `|-------|----------|\n`;
  response += `| Entry | ${data.prices.entry.toFixed(2)} |\n`;
  response += `| Target | ${data.prices.target.toFixed(2)} |\n`;
  response += `| Stop Loss | ${data.prices.stop_loss.toFixed(2)} |\n`;
  response += `| **Risk/Reward** | **${data.prices.risk_reward.toFixed(2)}** |\n\n`;

  // Hold period
  response += `### Recommended Hold Period\n`;
  response += `${data.hold_period.min_days} - ${data.hold_period.max_days} days\n\n`;

  // Score breakdown
  response += `### Score Breakdown\n`;
  response += `| Component | Score | Weight |\n`;
  response += `|-----------|-------|--------|\n`;

  const scoreKeys = Object.keys(data.scores);
  for (const key of scoreKeys) {
    const score = data.scores[key];
    const weight = data.weights[key] || 0;
    const label = key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
    response += `| ${label} | ${score.toFixed(3)} | ${(weight * 100).toFixed(0)}% |\n`;
  }

  // Warnings
  if (data.warnings && data.warnings.length > 0) {
    response += `\n### ⚠️ Warnings\n`;
    for (const warning of data.warnings) {
      response += `- ${warning}\n`;
    }
  }

  response += `\n*Note: This analysis is for informational purposes only, not financial advice.*`;

  return response;
}

/**
 * Format NLQ results as a readable response
 */
function formatNLQResponse(data: NLQResponse): string {
  if (!data.success || data.count === 0) {
    return `I couldn't find any stocks matching your query. Try rephrasing or use queries like:
- "show all bank stocks"
- "stocks with RSI above 70"
- "top 10 stocks by volume"`;
  }

  let response = `**${data.interpretation}**\n\n`;

  // Format results based on what fields are available
  const results = data.results.slice(0, 10); // Limit display

  if (results.length > 0) {
    const sample = results[0];

    // Check what type of data we have
    if ("signal_type" in sample) {
      // Signal data
      response += "| Ticker | Signal | Confidence | Score |\n";
      response += "|--------|--------|------------|-------|\n";
      for (const r of results) {
        const ticker = r.ticker || "N/A";
        const signal = r.signal_type || r.signal || "N/A";
        const confidence =
          typeof r.confidence === "number"
            ? `${(r.confidence * 100).toFixed(0)}%`
            : "N/A";
        const score =
          typeof r.total_score === "number"
            ? r.total_score.toFixed(2)
            : typeof r.score === "number"
              ? r.score.toFixed(2)
              : "N/A";
        response += `| ${ticker} | ${signal} | ${confidence} | ${score} |\n`;
      }
    } else if ("value" in sample) {
      // Indicator/ranking data
      response += "| Ticker | Value | Sector |\n";
      response += "|--------|-------|--------|\n";
      for (const r of results) {
        const ticker = r.ticker || "N/A";
        const value =
          typeof r.value === "number" ? r.value.toFixed(2) : String(r.value);
        const sector = r.sector || "N/A";
        response += `| ${ticker} | ${value} | ${sector} |\n`;
      }
    } else {
      // Generic data - show as key-value
      for (const r of results) {
        const ticker = r.ticker || "Unknown";
        response += `- **${ticker}**`;
        if (r.sector) response += ` (${r.sector})`;
        if (r.close) response += ` - Price: ৳${Number(r.close).toFixed(2)}`;
        response += "\n";
      }
    }

    if (data.count > 10) {
      response += `\n*Showing 10 of ${data.count} results*`;
    }
  }

  response +=
    "\n\n*Note: This data is for informational purposes only, not financial advice.*";

  return response;
}

/**
 * Helper to create a streaming response for formatted text
 */
function createTextStreamResponse(text: string): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Send formatted response as AI SDK data stream format
      const dataLine = `0:${JSON.stringify(text)}\n`;
      controller.enqueue(encoder.encode(dataLine));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}

/**
 * POST handler for chat messages
 */
export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    // Get the latest user message
    const lastMessage = messages[messages.length - 1];
    const userQuery = lastMessage?.content || "";

    // Check if this is a single stock analysis query (e.g., "analyze GP")
    const analyzeTicker = extractAnalyzeTicker(userQuery);
    if (analyzeTicker) {
      const analyzeResult = await executeAnalyzeQuery(analyzeTicker);

      if (analyzeResult.success && analyzeResult.data) {
        const formattedResponse = formatAnalyzeResponse(analyzeResult.data);
        return createTextStreamResponse(formattedResponse);
      }

      // If analyze failed, return error message
      if (analyzeResult.error) {
        const errorResponse = `I couldn't analyze **${analyzeTicker}**. ${analyzeResult.error}\n\nMake sure the ticker symbol is correct and the stock has sufficient trading data.`;
        return createTextStreamResponse(errorResponse);
      }
    }

    // Check if this is a stock data query (multiple stocks)
    if (isStockQuery(userQuery)) {
      // Try NLQ endpoint first
      const nlqResult = await executeNLQQuery(userQuery);

      if (nlqResult.success && nlqResult.data) {
        // Return formatted stock data as a stream
        const formattedResponse = formatNLQResponse(nlqResult.data);
        return createTextStreamResponse(formattedResponse);
      }

      // If NLQ failed, continue to AI response with context about the error
      if (nlqResult.error) {
        console.log("NLQ query failed, falling back to AI:", nlqResult.error);
      }
    }

    // For non-stock queries or NLQ failures, use AI
    const result = streamText({
      model: openai(process.env.OPENAI_MODEL || "gpt-3.5-turbo"),
      system: SYSTEM_PROMPT,
      messages,
    });

    return result.toDataStreamResponse();
  } catch (error) {
    console.error("Chat API error:", error);

    return new Response(
      JSON.stringify({
        error: "Failed to process chat request",
        details: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}
