import { createClient } from "@/lib/supabase/server";
import { getStrategiesWithSignals, createStrategy } from "@/lib/db/strategies";
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

    const strategies = await getStrategiesWithSignals(user.id);

    return NextResponse.json({
      strategies,
    });
  } catch (error) {
    console.error("Error fetching strategies:", error);
    return NextResponse.json(
      { error: "Failed to fetch strategies" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { userId: bodyUserId, ...strategyData } = body;

    if (bodyUserId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const strategy = await createStrategy(user.id, strategyData);

    return NextResponse.json({
      strategy,
    });
  } catch (error) {
    console.error("Error creating strategy:", error);
    return NextResponse.json(
      { error: "Failed to create strategy" },
      { status: 500 }
    );
  }
}
