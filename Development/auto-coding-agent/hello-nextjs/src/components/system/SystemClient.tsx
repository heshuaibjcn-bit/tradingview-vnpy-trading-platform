"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Activity,
  Server,
  Cpu,
  HardDrive,
  MemoryStick,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Trash2,
  RotateCw,
  Settings,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface SystemClientProps {
  userId: string;
}

interface ServiceStatus {
  name: string;
  service_type: string;
  healthy: boolean;
  level: string;
  message: string;
  uptime_seconds: number;
  error_count: number;
  last_check: string;
}

interface HealthData {
  status: string;
  services: Record<string, ServiceStatus>;
  system_info: {
    cpu_percent: number;
    memory_percent: number;
    memory_available_mb: number;
    memory_total_mb: number;
    disk_percent: number;
    disk_free_gb: number;
    disk_total_gb: number;
    uptime_seconds: number;
  };
  alerts: string[];
  timestamp: string;
  service_count: number;
  healthy_count: number;
  unhealthy_count: number;
}

interface LogEntry {
  timestamp: string;
  level: string;
  service: string;
  message: string;
}

type TabType = "overview" | "services" | "logs" | "system";

export function SystemClient({ userId }: SystemClientProps) {
  // userId is used for authentication in parent component
  void userId;

  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [logFilter, setLogFilter] = useState<"all" | "error" | "warning">("all");
  const hasInitialized = useRef(false);

  const fetchHealthData = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        setHealthData(data.data);
      }
    } catch (error) {
      console.error("Failed to fetch health data:", error);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const level = logFilter !== "all" ? logFilter : undefined;
      const res = await fetch(`/api/health?action=logs${level ? `&level=${level}` : ""}`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  }, [logFilter]);

  const fetchData = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchHealthData(), fetchLogs()]);
    setLoading(false);
    setRefreshing(false);
  }, [fetchHealthData, fetchLogs]);

  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchData();
      // Refresh every 30 seconds
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [fetchData]);

  useEffect(() => {
    if (hasInitialized.current && activeTab === "logs") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchLogs();
    }
  }, [activeTab, fetchLogs]);

  const handleRestartService = async (service: string) => {
    if (!confirm(`确定要重启服务 "${service}" 吗？`)) return;

    try {
      const res = await fetch("/api/health", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "restart_service", service }),
      });

      if (res.ok) {
        alert("服务已重启");
        fetchData();
      }
    } catch (error) {
      console.error("Failed to restart service:", error);
      alert("重启失败");
    }
  };

  const handleClearLogs = async () => {
    if (!confirm("确定要清空所有日志吗？")) return;

    try {
      const res = await fetch("/api/health", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "clear_logs" }),
      });

      if (res.ok) {
        setLogs([]);
        alert("日志已清空");
      }
    } catch (error) {
      console.error("Failed to clear logs:", error);
      alert("清空失败");
    }
  };

  const getStatusIcon = (healthy: boolean, level: string) => {
    if (!healthy || level === "critical") {
      return <XCircle className="h-5 w-5 text-red-400" />;
    }
    if (level === "degraded") {
      return <AlertTriangle className="h-5 w-5 text-yellow-400" />;
    }
    return <CheckCircle2 className="h-5 w-5 text-green-400" />;
  };

  const getStatusColor = (level: string) => {
    switch (level) {
      case "healthy": return "text-green-400";
      case "degraded": return "text-yellow-400";
      case "unhealthy": return "text-orange-400";
      case "critical": return "text-red-400";
      default: return "text-zinc-400";
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}天 ${hours}时`;
    if (hours > 0) return `${hours}时 ${mins}分`;
    return `${mins}分钟`;
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case "debug": return "text-zinc-400";
      case "info": return "text-blue-400";
      case "warning": return "text-yellow-400";
      case "error": return "text-orange-400";
      case "critical": return "text-red-400";
      default: return "text-zinc-400";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">系统监控</h1>
          <p className="text-sm text-zinc-500 mt-1">实时监控系统运行状态</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
          title="刷新"
        >
          <RefreshCw className={`h-5 w-5 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Overall Status */}
      {healthData && (
        <div className={`border rounded-lg p-6 ${
          healthData.status === "healthy"
            ? "border-green-500/30 bg-green-500/10"
            : healthData.status === "critical"
            ? "border-red-500/30 bg-red-500/10"
            : "border-yellow-500/30 bg-yellow-500/10"
        }`}>
          <div className="flex items-center gap-4">
            {healthData.status === "healthy" ? (
              <CheckCircle2 className="h-8 w-8 text-green-400" />
            ) : healthData.status === "critical" ? (
              <XCircle className="h-8 w-8 text-red-400" />
            ) : (
              <AlertTriangle className="h-8 w-8 text-yellow-400" />
            )}
            <div>
              <h2 className="text-lg font-semibold text-zinc-100">
                系统状态: {healthData.status === "healthy" ? "正常" : healthData.status === "critical" ? "严重" : "警告"}
              </h2>
              <p className="text-sm text-zinc-500">
                {healthData.healthy_count}/{healthData.service_count} 个服务运行正常
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        <TabButton active={activeTab === "overview"} onClick={() => setActiveTab("overview")}>
          <Activity className="h-4 w-4 mr-2" />
          概览
        </TabButton>
        <TabButton active={activeTab === "services"} onClick={() => setActiveTab("services")}>
          <Server className="h-4 w-4 mr-2" />
          服务
        </TabButton>
        <TabButton active={activeTab === "logs"} onClick={() => setActiveTab("logs")}>
          <FileText className="h-4 w-4 mr-2" />
          日志
        </TabButton>
        <TabButton active={activeTab === "system"} onClick={() => setActiveTab("system")}>
          <Settings className="h-4 w-4 mr-2" />
          系统资源
        </TabButton>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === "overview" && healthData && (
            <div className="space-y-6">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <QuickStat
                  icon={<Cpu className="h-5 w-5 text-blue-400" />}
                  label="CPU"
                  value={`${healthData.system_info.cpu_percent.toFixed(1)}%`}
                />
                <QuickStat
                  icon={<MemoryStick className="h-5 w-5 text-green-400" />}
                  label="内存"
                  value={`${healthData.system_info.memory_percent.toFixed(1)}%`}
                />
                <QuickStat
                  icon={<HardDrive className="h-5 w-5 text-yellow-400" />}
                  label="磁盘"
                  value={`${healthData.system_info.disk_percent.toFixed(1)}%`}
                />
                <QuickStat
                  icon={<Server className="h-5 w-5 text-zinc-400" />}
                  label="运行时间"
                  value={formatUptime(healthData.system_info.uptime_seconds)}
                />
              </div>

              {/* Services List */}
              <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                <h3 className="text-lg font-semibold text-zinc-100 mb-4">服务状态</h3>
                <div className="space-y-3">
                  {Object.entries(healthData.services).map(([key, service]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between p-3 border border-zinc-800 rounded-lg hover:bg-zinc-800/50"
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon(service.healthy, service.level)}
                        <div>
                          <p className="text-sm font-medium text-zinc-200">{service.name}</p>
                          <p className="text-xs text-zinc-500">{service.message}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-zinc-500">运行时间</p>
                        <p className="text-sm text-zinc-300">{formatUptime(service.uptime_seconds)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Services Tab */}
          {activeTab === "services" && healthData && (
            <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900">
                    <TableHead>服务</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>消息</TableHead>
                    <TableHead>运行时间</TableHead>
                    <TableHead>错误次数</TableHead>
                    <TableHead>操作</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(healthData.services).map(([key, service]) => (
                    <tr key={key} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                      <td className="px-4 py-3 text-sm font-medium text-zinc-200">
                        {service.name}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(service.healthy, service.level)}
                          <span className={`text-sm ${getStatusColor(service.level)}`}>
                            {service.level}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-400">{service.message}</td>
                      <td className="px-4 py-3 text-sm text-zinc-300">
                        {formatUptime(service.uptime_seconds)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-sm ${service.error_count > 0 ? "text-red-400" : "text-zinc-400"}`}>
                          {service.error_count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {!service.healthy && (
                          <button
                            onClick={() => handleRestartService(key)}
                            className="p-1.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200"
                            title="重启服务"
                          >
                            <RotateCw className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === "logs" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <FilterButton
                    active={logFilter === "all"}
                    onClick={() => setLogFilter("all")}
                  >
                    全部
                  </FilterButton>
                  <FilterButton
                    active={logFilter === "warning"}
                    onClick={() => setLogFilter("warning")}
                  >
                    警告
                  </FilterButton>
                  <FilterButton
                    active={logFilter === "error"}
                    onClick={() => setLogFilter("error")}
                  >
                    错误
                  </FilterButton>
                </div>
                <button
                  onClick={handleClearLogs}
                  className="px-3 py-1.5 text-sm rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  清空
                </button>
              </div>

              <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50 max-h-96 overflow-y-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-zinc-900">
                    <tr className="border-b border-zinc-800">
                      <TableHead>时间</TableHead>
                      <TableHead>级别</TableHead>
                      <TableHead>服务</TableHead>
                      <TableHead>消息</TableHead>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="text-center py-8 text-zinc-500">
                          暂无日志
                        </td>
                      </tr>
                    ) : (
                      logs.map((log, i) => (
                        <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                          <td className="px-4 py-2 text-xs text-zinc-500">
                            {new Date(log.timestamp).toLocaleString("zh-CN")}
                          </td>
                          <td className="px-4 py-2">
                            <span className={`text-xs font-medium uppercase ${getLogColor(log.level)}`}>
                              {log.level}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-xs text-zinc-400">{log.service}</td>
                          <td className={`px-4 py-2 text-sm ${getLogColor(log.level)}`}>
                            {log.message}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* System Resources Tab */}
          {activeTab === "system" && healthData && (
            <div className="space-y-6">
              {/* CPU */}
              <ResourceBar
                label="CPU 使用率"
                value={healthData.system_info.cpu_percent}
                color={healthData.system_info.cpu_percent > 80 ? "text-red-400" : "text-blue-400"}
              />

              {/* Memory */}
              <ResourceBar
                label="内存使用率"
                value={healthData.system_info.memory_percent}
                color={healthData.system_info.memory_percent > 80 ? "text-red-400" : "text-green-400"}
              />
              <div className="flex justify-between text-sm text-zinc-500 px-4">
                <span>可用: {healthData.system_info.memory_available_mb} MB</span>
                <span>总计: {healthData.system_info.memory_total_mb} MB</span>
              </div>

              {/* Disk */}
              <ResourceBar
                label="磁盘使用率"
                value={healthData.system_info.disk_percent}
                color={healthData.system_info.disk_percent > 90 ? "text-red-400" : "text-yellow-400"}
              />
              <div className="flex justify-between text-sm text-zinc-500 px-4">
                <span>可用: {healthData.system_info.disk_free_gb.toFixed(1)} GB</span>
                <span>总计: {healthData.system_info.disk_total_gb} GB</span>
              </div>

              {/* Uptime */}
              <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-zinc-500">系统运行时间</span>
                  <span className="text-lg font-semibold text-zinc-200">
                    {formatUptime(healthData.system_info.uptime_seconds)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Helper components
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 font-medium transition-colors flex items-center ${
        active
          ? "text-blue-400 border-b-2 border-blue-400"
          : "text-zinc-500 hover:text-zinc-300"
      }`}
    >
      {children}
    </button>
  );
}

function TableHead({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">{children}</th>;
}

function QuickStat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-zinc-500">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-zinc-100">{value}</p>
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
        active
          ? "bg-zinc-700 text-zinc-200"
          : "text-zinc-500 hover:text-zinc-300"
      }`}
    >
      {children}
    </button>
  );
}

function ResourceBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-zinc-500">{label}</span>
        <span className={`text-lg font-semibold ${color}`}>{value.toFixed(1)}%</span>
      </div>
      <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${color.replace("text-", "bg-")}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}
