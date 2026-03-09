import { createClient } from "@/lib/supabase/server";
import { createOrder } from "@/lib/db/orders";
import { NextResponse } from "next/server";

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
    const { userId: bodyUserId, symbol, side, orderType, price, quantity } = body;

    // Verify user ID matches
    if (bodyUserId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Validate required fields
    if (!symbol || !side || !quantity) {
      return NextResponse.json(
        { error: "Missing required fields: symbol, side, quantity" },
        { status: 400 }
      );
    }

    // Validate side
    if (side !== "buy" && side !== "sell") {
      return NextResponse.json(
        { error: "Invalid side: must be 'buy' or 'sell'" },
        { status: 400 }
      );
    }

    // Validate order type
    if (orderType !== "limit" && orderType !== "market") {
      return NextResponse.json(
        { error: "Invalid orderType: must be 'limit' or 'market'" },
        { status: 400 }
      );
    }

    // For limit orders, price is required
    if (orderType === "limit" && (!price || price <= 0)) {
      return NextResponse.json(
        { error: "Limit orders must have a valid price" },
        { status: 400 }
      );
    }

    // Validate quantity
    if (quantity <= 0) {
      return NextResponse.json(
        { error: "Quantity must be greater than 0" },
        { status: 400 }
      );
    }

    // Create the order
    const order = await createOrder(user.id, {
      symbol: symbol.toUpperCase(),
      side,
      quantity,
      price: orderType === "limit" ? price : 0,
      status: "pending",
      filled_quantity: 0,
    });

    return NextResponse.json({
      status: "ok",
      order,
    });
  } catch (error) {
    console.error("Error creating order:", error);
    return NextResponse.json(
      { error: "Failed to create order" },
      { status: 500 }
    );
  }
}
