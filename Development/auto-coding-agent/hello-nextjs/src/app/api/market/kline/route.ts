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
    const period = searchParams.get("period") || "101"; // 101=daily
    const count = parseInt(searchParams.get("count") || "100");

    if (!symbol) {
      return NextResponse.json(
        { error: "Symbol is required" },
        { status: 400 }
      );
    }

    // Fetch K-line data from Python backend
    const params = new URLSearchParams({
      symbol,
      period,
      count: count.toString(),
    });

    const response = await fetch(`${PYTHON_API_URL}/api/kline?${params}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Python API error:", errorData);

      return NextResponse.json(
        {
          error: "K-line data service unavailable",
          message: "Unable to fetch K-line data. Please ensure the Python backend is running.",
          details: errorData.detail || "Unknown error",
        },
        { status: 503 }
      );
    }

    const data = await response.json();

    // Return the K-line data
    return NextResponse.json({
      symbol: data.symbol,
      period: data.period,
      data: data.data,
    });
  } catch (error) {
    console.error("Error fetching K-line:", error);
    return NextResponse.json(
      {
        error: "Failed to fetch K-line data",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
