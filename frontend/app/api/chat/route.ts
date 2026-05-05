import { NextRequest } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Next.js API route that proxies chat SSE requests to the FastAPI backend.
 * This avoids CORS issues in production when both services share the same origin.
 */
export async function POST(req: NextRequest) {
  const body = await req.json();

  const backendUrl = `${API_URL}/api/chat`;

  // Forward request to backend as SSE
  const backendResponse = await fetch(backendUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      "Cache-Control": "no-cache",
    },
    body: JSON.stringify(body),
  });

  if (!backendResponse.ok) {
    const error = await backendResponse.text().catch(() => "Unknown error");
    return new Response(JSON.stringify({ error }), {
      status: backendResponse.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Stream the SSE response directly to the client
  return new Response(backendResponse.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
