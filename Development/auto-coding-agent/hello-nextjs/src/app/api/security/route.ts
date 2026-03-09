import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Emergency stop state
const emergencyStopState = {
  active: false,
  userId: null as string | null,
  reason: null as string | null,
  timestamp: null as string | null,
};

// Sensitive operations log
const sensitiveOpsLog: Array<{
  id: string;
  userId: string;
  operation: string;
  details: Record<string, unknown>;
  timestamp: string;
  ip: string;
  success: boolean;
}> = [];

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
      return NextResponse.json({
        status: "ok",
        emergencyStop: emergencyStopState.active,
        emergencyStopReason: emergencyStopState.reason,
        emergencyStopTime: emergencyStopState.timestamp,
      });
    }

    if (action === "logs") {
      const userLogs = sensitiveOpsLog.filter((log) => log.userId === user.id);
      return NextResponse.json({
        status: "ok",
        logs: userLogs.slice(-100),
      });
    }

    if (action === "permissions") {
      // Mock permissions - in production this would come from database
      return NextResponse.json({
        status: "ok",
        permissions: {
          canTrade: true,
          canUseStrategies: true,
          canModifySettings: true,
          canExportData: true,
          emergencyStopEnabled: true,
        },
      });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Security API error:", error);
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 });
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
    const { userId: bodyUserId, action, password, ...rest } = body;

    if (bodyUserId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    if (action === "confirm_trade") {
      // Verify trade password (mock - in production this would check a stored hash)
      const isValidPassword = password === "123456"; // Demo password

      if (isValidPassword) {
        return NextResponse.json({
          status: "ok",
          confirmed: true,
          message: "交易已确认",
        });
      } else {
        return NextResponse.json({
          status: "error",
          message: "交易密码错误",
        }, { status: 401 });
      }
    }

    if (action === "emergency_stop") {
      emergencyStopState.active = true;
      emergencyStopState.userId = user.id;
      emergencyStopState.reason = rest.reason || "手动触发";
      emergencyStopState.timestamp = new Date().toISOString();

      sensitiveOpsLog.push({
        id: `ops_${Date.now()}`,
        userId: user.id,
        operation: "emergency_stop",
        details: { reason: rest.reason || "手动触发" },
        timestamp: new Date().toISOString(),
        ip: request.headers.get("x-forwarded-for") || "unknown",
        success: true,
      });

      return NextResponse.json({
        status: "ok",
        message: "紧急停止已激活",
      });
    }

    if (action === "reset_emergency_stop") {
      if (!emergencyStopState.active) {
        return NextResponse.json({
          status: "error",
          message: "紧急停止未激活",
        }, { status: 400 });
      }

      if (password !== "123456") {
        return NextResponse.json({
          status: "error",
          message: "交易密码错误",
        }, { status: 401 });
      }

      sensitiveOpsLog.push({
        id: `ops_${Date.now()}`,
        userId: user.id,
        operation: "reset_emergency_stop",
        details: {},
        timestamp: new Date().toISOString(),
        ip: request.headers.get("x-forwarded-for") || "unknown",
        success: true,
      });

      emergencyStopState.active = false;
      emergencyStopState.userId = null;
      emergencyStopState.reason = null;
      emergencyStopState.timestamp = null;

      return NextResponse.json({
        status: "ok",
        message: "紧急停止已解除",
      });
    }

    if (action === "set_password") {
      const { newPassword } = rest;

      if (!newPassword || newPassword.length < 6) {
        return NextResponse.json({
          status: "error",
          message: "密码长度至少为6位",
        }, { status: 400 });
      }

      sensitiveOpsLog.push({
        id: `ops_${Date.now()}`,
        userId: user.id,
        operation: "password_changed",
        details: {},
        timestamp: new Date().toISOString(),
        ip: request.headers.get("x-forwarded-for") || "unknown",
        success: true,
      });

      return NextResponse.json({
        status: "ok",
        message: "交易密码已设置",
      });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Security POST error:", error);
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 });
  }
}
