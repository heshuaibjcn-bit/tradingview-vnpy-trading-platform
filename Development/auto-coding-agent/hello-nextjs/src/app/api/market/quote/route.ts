import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Python backend API URL
const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://127.0.0.1:8000";

export async function GET(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get("symbol");

    if (!symbol) {
      return NextResponse.json(
        { error: "Symbol is required" },
        { status: 400 }
      );
    }

    // Fetch real market data from Python backend
    const response = await fetch(`${PYTHON_API_URL}/api/quote?symbol=${symbol}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      // Add cache control to prevent stale data
      cache: "no-store",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Python API error:", errorData);

      // Return a fallback response if backend is unavailable
      return NextResponse.json(
        {
          error: "Market data service unavailable",
          message: "Unable to fetch real-time data. Please ensure the Python backend is running.",
          details: errorData.detail || "Unknown error",
        },
        { status: 503 }
      );
    }

    const data = await response.json();

    // Transform the response to match frontend expectations
    return NextResponse.json({
      symbol: data.symbol,
      name: data.name || "",
      price: data.price,
      change: data.change,
      change_percent: data.change_percent,
      open: data.open,
      high: data.high,
      low: data.low,
      volume: data.volume,
      amount: data.amount,
      bid_price: data.bid_price,
      ask_price: data.ask_price,
      timestamp: data.timestamp,
    });
  } catch (error) {
    console.error("Error fetching quote:", error);
    return NextResponse.json(
      {
        error: "Failed to fetch quote",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
