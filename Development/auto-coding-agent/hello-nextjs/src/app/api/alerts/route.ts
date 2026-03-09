import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// In-memory storage for demo (in production, use database)
const alertRules = new Map<string, AlertRule>();
const alertHistory: AlertHistoryItem[] = [];
let alertIdCounter = 1;

interface AlertRule {
  id: string;
  userId: string;
  symbol: string;
  alertType: string;
  threshold: number;
  name: string;
  description: string;
  enabled: boolean;
  createdAt: string;
}

interface AlertHistoryItem {
  id: string;
  userId: string;
  symbol: string;
  alertType: string;
  message: string;
  value: number;
  threshold: number;
  triggeredAt: string;
  acknowledged: boolean;
}

// Alert types configuration
const ALERT_TYPES = {
  price_above: { name: "价格突破上限", description: "当价格突破设定值时提醒" },
  price_below: { name: "价格跌破下限", description: "当价格跌破设定值时提醒" },
  price_change: { name: "价格异动", description: "当价格变化超过百分比时提醒" },
  volume_spike: { name: "成交量异常", description: "当成交量激增时提醒" },
  rsi_overbought: { name: "RSI超买", description: "当RSI超过设定值时提醒" },
  rsi_oversold: { name: "RSI超卖", description: "当RSI低于设定值时提醒" },
};

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("userId");
    const action = searchParams.get("action"); // "rules" or "history"

    if (!userId) {
      return NextResponse.json({ error: "Missing userId" }, { status: 400 });
    }

    if (action === "history") {
      // Get alert history
      const userAlerts = alertHistory
        .filter(a => a.userId === userId)
        .sort((a, b) => new Date(b.triggeredAt).getTime() - new Date(a.triggeredAt).getTime())
        .slice(0, 100);

      return NextResponse.json({ alerts: userAlerts });
    }

    // Get alert rules (default)
    const userRules = Array.from(alertRules.values()).filter(r => r.userId === userId);
    return NextResponse.json({ rules: userRules, types: ALERT_TYPES });
  } catch (error) {
    console.error("Alerts GET error:", error);
    return NextResponse.json({ error: "Failed to fetch alerts" }, { status: 500 });
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
    const { action, userId, ...data } = body;

    if (userId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    if (action === "create") {
      // Create new alert rule
      const ruleId = `rule_${Date.now()}_${alertIdCounter++}`;
      const rule = {
        id: ruleId,
        userId: user.id,
        ...data,
        enabled: true,
        createdAt: new Date().toISOString(),
      };
      alertRules.set(ruleId, rule);

      return NextResponse.json({ status: "ok", rule });
    }

    if (action === "test") {
      // Trigger a test alert
      const testAlert = {
        id: `alert_${Date.now()}`,
        ruleId: "test_rule",
        userId: user.id,
        symbol: data.symbol || "600519",
        alertType: data.alertType || "price_above",
        message: "测试告警：这是一条测试消息",
        value: 10.50,
        threshold: 10.00,
        triggeredAt: new Date().toISOString(),
        acknowledged: false,
      };
      alertHistory.unshift(testAlert);

      return NextResponse.json({ status: "ok", alert: testAlert });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Alerts POST error:", error);
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const ruleId = searchParams.get("ruleId");

    if (!ruleId) {
      return NextResponse.json({ error: "Missing ruleId" }, { status: 400 });
    }

    const rule = alertRules.get(ruleId);
    if (!rule || rule.userId !== user.id) {
      return NextResponse.json({ error: "Rule not found" }, { status: 404 });
    }

    alertRules.delete(ruleId);

    return NextResponse.json({ status: "ok" });
  } catch (error) {
    console.error("Alerts DELETE error:", error);
    return NextResponse.json({ error: "Failed to delete rule" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { ruleId, userId, ...updates } = body;

    if (userId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const rule = alertRules.get(ruleId);
    if (!rule || rule.userId !== user.id) {
      return NextResponse.json({ error: "Rule not found" }, { status: 404 });
    }

    // Update rule
    const updatedRule = { ...rule, ...updates };
    alertRules.set(ruleId, updatedRule);

    return NextResponse.json({ status: "ok", rule: updatedRule });
  } catch (error) {
    console.error("Alerts PATCH error:", error);
    return NextResponse.json({ error: "Failed to update rule" }, { status: 500 });
  }
}
