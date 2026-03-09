import { createClient } from "@/lib/supabase/server";
import { updateStrategy, deleteStrategy, getStrategyById } from "@/lib/db/strategies";
import { NextResponse } from "next/server";

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const body = await request.json();

    // Verify ownership
    await getStrategyById(id, user.id);

    const strategy = await updateStrategy(id, user.id, body);

    return NextResponse.json({
      strategy,
    });
  } catch (error: unknown) {
    console.error("Error updating strategy:", error);
    if (error instanceof Error && error.message === "Strategy not found") {
      return NextResponse.json({ error: "Strategy not found" }, { status: 404 });
    }
    return NextResponse.json(
      { error: "Failed to update strategy" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    // Verify ownership
    await getStrategyById(id, user.id);

    await deleteStrategy(id, user.id);

    return NextResponse.json({
      success: true,
    });
  } catch (error: unknown) {
    console.error("Error deleting strategy:", error);
    if (error instanceof Error && error.message === "Strategy not found") {
      return NextResponse.json({ error: "Strategy not found" }, { status: 404 });
    }
    return NextResponse.json(
      { error: "Failed to delete strategy" },
      { status: 500 }
    );
  }
}
