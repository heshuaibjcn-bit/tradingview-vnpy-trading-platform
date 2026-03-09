import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Risk configuration storage (in-memory for demo)
const riskConfigs = new Map<string, {
  maxPositionValue: number;
  maxPositionPct: number;
  maxTotalPositions: number;
  maxTotalExposure: number;
  stopLossEnabled: boolean;
  stopLossPct: number;
  takeProfitPct: number;
  maxDailyTrades: number;
  maxDailyLossPct: number;
}>();

// Default configuration
const DEFAULT_CONFIG = {
  maxPositionValue: 100000,
  maxPositionPct: 0.30,
  maxTotalPositions: 10,
  maxTotalExposure: 0.95,
  stopLossEnabled: true,
  stopLossPct: 0.05,
  takeProfitPct: 0.15,
  maxDailyTrades: 50,
  maxDailyLossPct: 0.05,
};

// Simulated daily tracking
const dailyTracking = {
  tradesToday: 0,
  lossToday: 0,
  turnoverToday: 0,
};

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
    const action = searchParams.get("action");

    if (action === "status") {
      // Get current risk status
      const config = riskConfigs.get(user.id) || DEFAULT_CONFIG;
      const exposure = 0.65; // Simulated current exposure
      const dailyLossPct = dailyTracking.lossToday / 100000;

      return NextResponse.json({
        status: "ok",
        summary: {
          positionLimits: {
            maxPositionValue: config.maxPositionValue,
            maxPositionPct: `${(config.maxPositionPct * 100).toFixed(0)}%`,
            maxTotalPositions: config.maxTotalPositions,
            maxTotalExposure: `${(config.maxTotalExposure * 100).toFixed(0)}%`,
            currentExposure: `${(exposure * 100).toFixed(1)}%`,
          },
          tradingLimits: {
            maxDailyTrades: config.maxDailyTrades,
            tradesToday: dailyTracking.tradesToday,
            maxDailyLoss: `${(config.maxDailyLossPct * 100).toFixed(1)}%`,
            lossToday: `${(dailyLossPct * 100).toFixed(2)}%`,
          },
          stopLoss: {
            enabled: config.stopLossEnabled,
            stopLoss: `${(config.stopLossPct * 100).toFixed(1)}%`,
            takeProfit: `${(config.takeProfitPct * 100).toFixed(1)}%`,
          },
        },
      });
    }

    // Get user's risk configuration
    const config = riskConfigs.get(user.id) || DEFAULT_CONFIG;
    return NextResponse.json({ status: "ok", config });
  } catch (error) {
    console.error("Risk GET error:", error);
    return NextResponse.json({ error: "Failed to fetch risk configuration" }, { status: 500 });
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
    const { userId, action, ...config } = body;

    if (userId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    if (action === "update") {
      // Update risk configuration
      const newConfig = {
        maxPositionValue: config.maxPositionValue ?? DEFAULT_CONFIG.maxPositionValue,
        maxPositionPct: (config.maxPositionPct ?? 30) / 100,
        maxTotalPositions: config.maxTotalPositions ?? DEFAULT_CONFIG.maxTotalPositions,
        maxTotalExposure: (config.maxTotalExposure ?? 95) / 100,
        stopLossEnabled: config.stopLossEnabled ?? true,
        stopLossPct: (config.stopLossPct ?? 5) / 100,
        takeProfitPct: (config.takeProfitPct ?? 15) / 100,
        maxDailyTrades: config.maxDailyTrades ?? DEFAULT_CONFIG.maxDailyTrades,
        maxDailyLossPct: (config.maxDailyLossPct ?? 5) / 100,
      };

      riskConfigs.set(user.id, newConfig);

      return NextResponse.json({ status: "ok", config: newConfig });
    }

    if (action === "check") {
      // Simulated trade risk check
      const riskConfig = riskConfigs.get(user.id) || DEFAULT_CONFIG;
      const { quantity, price } = config;

      const positionValue = quantity * price;
      const warnings = [];

      // Check position value
      if (positionValue > riskConfig.maxPositionValue) {
        return NextResponse.json({
          status: "rejected",
          reason: `Position value ¥${positionValue.toLocaleString()} exceeds limit ¥${riskConfig.maxPositionValue.toLocaleString()}`,
        });
      }

      // Check daily trades
      if (dailyTracking.tradesToday >= riskConfig.maxDailyTrades) {
        return NextResponse.json({
          status: "rejected",
          reason: `Daily trade limit (${riskConfig.maxDailyTrades}) reached`,
        });
      }

      // Generate warnings
      if (positionValue > riskConfig.maxPositionValue * 0.9) {
        warnings.push("Position size approaching limit");
      }

      if (dailyTracking.tradesToday >= riskConfig.maxDailyTrades * 0.9) {
        warnings.push("Approaching daily trade limit");
      }

      return NextResponse.json({
        status: "approved",
        warnings,
      });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Risk POST error:", error);
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 });
  }
}
