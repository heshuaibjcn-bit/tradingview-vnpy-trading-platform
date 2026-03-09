import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

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

    // TODO: Fetch real market data from broker API
    // For now, return a mock price based on symbol hash
    const hash = symbol.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const mockPrice = (hash % 1000) / 10 + 10; // Generate a price between 10 and 110

    return NextResponse.json({
      symbol: symbol.toUpperCase(),
      price: mockPrice,
      change: (Math.random() * 4 - 2).toFixed(2), // Random change between -2% and +2%
      volume: Math.floor(Math.random() * 1000000),
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error fetching quote:", error);
    return NextResponse.json(
      { error: "Failed to fetch quote" },
      { status: 500 }
    );
  }
}
