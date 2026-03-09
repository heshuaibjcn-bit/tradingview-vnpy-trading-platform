import { createClient } from "@/lib/supabase/server";
import { getPositions, getPortfolioValue } from "@/lib/db/positions";
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
    const userId = searchParams.get("userId");

    if (userId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const positions = await getPositions(user.id);
    const portfolio = await getPortfolioValue(user.id);

    return NextResponse.json({
      positions,
      portfolio,
    });
  } catch (error) {
    console.error("Error fetching positions:", error);
    return NextResponse.json(
      { error: "Failed to fetch positions" },
      { status: 500 }
    );
  }
}
