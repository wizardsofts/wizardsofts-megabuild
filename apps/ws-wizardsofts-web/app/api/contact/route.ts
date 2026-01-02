import { NextRequest, NextResponse } from "next/server";
import { createContactSubmission } from "@/lib/contactRepo";
import { checkRateLimit, isSpam } from "@/lib/rateLimiter";

// Email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Helper to get client IP
function getClientIp(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-for");
  const realIp = request.headers.get("x-real-ip");

  if (forwarded) {
    return forwarded.split(",")[0].trim();
  }

  if (realIp) {
    return realIp;
  }

  return "unknown";
}

// POST /api/contact - Create a new contact submission
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Check honeypot field (must be named differently in actual form)
    if (isSpam(body.website || body.url || body._gotcha)) {
      return NextResponse.json({ error: "Invalid submission" }, { status: 400 });
    }

    // Get client IP for rate limiting
    const clientIp = getClientIp(request);

    // Check rate limit
    if (!checkRateLimit(clientIp)) {
      return NextResponse.json(
        { error: "Too many requests. Please try again later." },
        { status: 429 }
      );
    }

    // Validate required fields
    if (!body.name || typeof body.name !== "string") {
      return NextResponse.json({ error: "Name is required and must be a string" }, { status: 400 });
    }

    if (!body.email || typeof body.email !== "string") {
      return NextResponse.json(
        { error: "Email is required and must be a string" },
        { status: 400 }
      );
    }

    if (!EMAIL_REGEX.test(body.email)) {
      return NextResponse.json({ error: "Invalid email format" }, { status: 400 });
    }

    if (!body.subject || typeof body.subject !== "string") {
      return NextResponse.json(
        { error: "Subject is required and must be a string" },
        { status: 400 }
      );
    }

    if (!body.message || typeof body.message !== "string") {
      return NextResponse.json(
        { error: "Message is required and must be a string" },
        { status: 400 }
      );
    }

    // Validate field lengths
    if (body.name.length > 255) {
      return NextResponse.json({ error: "Name must be less than 255 characters" }, { status: 400 });
    }

    if (body.email.length > 320) {
      return NextResponse.json(
        { error: "Email must be less than 320 characters" },
        { status: 400 }
      );
    }

    if (body.company && body.company.length > 255) {
      return NextResponse.json(
        { error: "Company must be less than 255 characters" },
        { status: 400 }
      );
    }

    if (body.subject.length > 255) {
      return NextResponse.json(
        { error: "Subject must be less than 255 characters" },
        { status: 400 }
      );
    }

    // Create submission
    const submission = await createContactSubmission({
      name: body.name.trim(),
      email: body.email.trim().toLowerCase(),
      company: body.company?.trim(),
      subject: body.subject.trim(),
      message: body.message.trim(),
      consent: Boolean(body.consent),
      ipAddress: clientIp,
      userAgent: request.headers.get("user-agent") || undefined,
      meta: body.meta,
    });

    // Return created submission (exclude sensitive fields)
    return NextResponse.json(
      {
        id: submission.id,
        name: submission.name,
        email: submission.email,
        company: submission.company,
        subject: submission.subject,
        message: submission.message,
        consent: submission.consent,
        submittedAt: submission.createdAt,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error creating contact submission:", error);

    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
