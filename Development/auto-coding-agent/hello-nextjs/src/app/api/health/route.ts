import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Service status storage
const serviceStatuses: Record<
  string,
  {
    name: string;
    service_type: string;
    healthy: boolean;
    level: string;
    message: string;
    uptime_seconds: number;
    error_count: number;
    last_check: string;
  }
> = {
  websocket: {
    name: "WebSocket Server",
    service_type: "websocket",
    healthy: true,
    level: "healthy",
    message: "Running on port 8765",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
  market_data: {
    name: "Market Data Service",
    service_type: "market_data",
    healthy: true,
    level: "healthy",
    message: "Receiving data",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
  strategy_engine: {
    name: "Strategy Engine",
    service_type: "strategy_engine",
    healthy: true,
    level: "healthy",
    message: "0 active strategies",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
  ths_client: {
    name: "Tonghuashun Client",
    service_type: "ths_client",
    healthy: true,
    level: "healthy",
    message: "Connected",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
  database: {
    name: "Database",
    service_type: "database",
    healthy: true,
    level: "healthy",
    message: "Connected",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
  alert_engine: {
    name: "Alert Engine",
    service_type: "alert_engine",
    healthy: true,
    level: "healthy",
    message: "Monitoring 0 rules",
    uptime_seconds: 3600,
    error_count: 0,
    last_check: new Date().toISOString(),
  },
};

// System log storage
const systemLogs: Array<{
  timestamp: string;
  level: string;
  service: string;
  message: string;
  details: Record<string, unknown>;
}> = [];

// System info
function getSystemInfo() {
  return {
    cpu_percent: Math.random() * 30 + 10,
    memory_percent: Math.random() * 20 + 40,
    memory_available_mb: 4000 + Math.floor(Math.random() * 2000),
    memory_total_mb: 16384,
    disk_percent: 85 + Math.random() * 5,
    disk_free_gb: 20 + Math.random() * 10,
    disk_total_gb: 512,
    uptime_seconds: 86400 + Math.floor(Math.random() * 3600),
  };
}

// Generate mock logs
function generateMockLogs(count = 50) {
  const services = Object.keys(serviceStatuses);
  const levels = ["debug", "info", "warning", "error", "critical"];
  const messages = {
    debug: ["Processing data", "Updating cache", "Running check"],
    info: ["Service started", "Connection established", "Data received"],
    warning: ["High latency", "Retry attempt", "Deprecated API usage"],
    error: ["Connection failed", "Data parse error", "Timeout"],
    critical: ["Service crash", "Database connection lost", "Out of memory"],
  };

  const logs = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const level = levels[Math.floor(Math.random() * levels.length)];
    const service = services[Math.floor(Math.random() * services.length)];
    const levelMessages = messages[level as keyof typeof messages];
    const message = levelMessages[Math.floor(Math.random() * levelMessages.length)];

    logs.push({
      timestamp: new Date(now - i * 60000 - Math.random() * 300000).toISOString(),
      level,
      service,
      message,
      details: {},
    });
  }

  return logs;
}

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

    // Update timestamps and generate dynamic data
    const now = new Date();
    Object.keys(serviceStatuses).forEach((key) => {
      serviceStatuses[key].last_check = now.toISOString();
      serviceStatuses[key].uptime_seconds += 30;
    });

    if (action === "logs") {
      const level = searchParams.get("level");
      const service = searchParams.get("service");
      const limit = parseInt(searchParams.get("limit") || "100");

      // Generate logs if empty
      if (systemLogs.length === 0) {
        systemLogs.push(...generateMockLogs(100));
      }

      let filteredLogs = [...systemLogs];

      if (level) {
        filteredLogs = filteredLogs.filter((l) => l.level === level);
      }
      if (service) {
        filteredLogs = filteredLogs.filter((l) => l.service === service);
      }

      return NextResponse.json({
        status: "ok",
        data: filteredLogs.slice(0, limit),
        total: filteredLogs.length,
      });
    }

    if (action === "system") {
      return NextResponse.json({
        status: "ok",
        data: getSystemInfo(),
      });
    }

    // Default: return full health status
    const systemInfo = getSystemInfo();
    const allHealthy = Object.values(serviceStatuses).every((s) => s.healthy);

    let overallStatus = "healthy";
    if (!allHealthy) {
      const hasCritical = Object.values(serviceStatuses).some((s) => s.level === "critical");
      overallStatus = hasCritical ? "critical" : "degraded";
    }

    return NextResponse.json({
      status: "ok",
      data: {
        status: overallStatus,
        services: serviceStatuses,
        system_info: systemInfo,
        alerts: [],
        timestamp: now.toISOString(),
        service_count: Object.keys(serviceStatuses).length,
        healthy_count: Object.values(serviceStatuses).filter((s) => s.healthy).length,
        unhealthy_count: Object.values(serviceStatuses).filter((s) => !s.healthy).length,
      },
    });
  } catch (error) {
    console.error("Health API error:", error);
    return NextResponse.json({ error: "Failed to fetch health status" }, { status: 500 });
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
    const { action, service } = body;

    if (action === "restart_service") {
      // Simulate service restart
      if (service && serviceStatuses[service]) {
        serviceStatuses[service].healthy = true;
        serviceStatuses[service].level = "healthy";
        serviceStatuses[service].message = "Service restarted";
        serviceStatuses[service].error_count = 0;
        serviceStatuses[service].uptime_seconds = 0;

        systemLogs.unshift({
          timestamp: new Date().toISOString(),
          level: "info",
          service: "system",
          message: `Service ${service} restarted by ${user.email}`,
          details: {},
        });

        return NextResponse.json({ status: "ok", message: `Service ${service} restarted` });
      }
      return NextResponse.json({ error: "Service not found" }, { status: 404 });
    }

    if (action === "clear_logs") {
      systemLogs.length = 0;
      return NextResponse.json({ status: "ok", message: "Logs cleared" });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Health POST error:", error);
    return NextResponse.json({ error: "Failed to process request" }, { status: 500 });
  }
}
