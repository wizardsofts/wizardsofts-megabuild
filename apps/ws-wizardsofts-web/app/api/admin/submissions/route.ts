import { NextRequest, NextResponse } from "next/server";
import { getContactSubmissions } from "@/lib/contactRepo";
import { logWarn, logInfo } from "@/lib/logger";

// GET /api/admin/submissions - List contact submissions (protected)
export async function GET(request: NextRequest) {
  try {
    // Check admin secret
    const adminSecret = request.headers.get("x-admin-secret");
    const expectedSecret = process.env.ADMIN_SECRET;

    if (!expectedSecret) {
      logWarn("ADMIN_SECRET not configured");
      return NextResponse.json({ error: "Admin endpoint not configured" }, { status: 503 });
    }

    if (!adminSecret || adminSecret !== expectedSecret) {
      logWarn("Unauthorized admin access attempt", {
        ip: request.headers.get("x-forwarded-for") || "unknown",
      });
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse query parameters
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get("limit") || "50");
    const offset = parseInt(searchParams.get("offset") || "0");

    // Validate parameters
    if (limit < 1 || limit > 100) {
      return NextResponse.json({ error: "Limit must be between 1 and 100" }, { status: 400 });
    }

    if (offset < 0) {
      return NextResponse.json({ error: "Offset must be non-negative" }, { status: 400 });
    }

    // Retrieve submissions
    const submissions = await getContactSubmissions(limit, offset);

    logInfo("Admin retrieved contact submissions", {
      count: submissions.length,
      limit,
      offset,
    });

    return NextResponse.json({
      submissions,
      pagination: {
        limit,
        offset,
        count: submissions.length,
      },
    });
  } catch (error) {
    console.error("Error retrieving contact submissions:", error);

    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
