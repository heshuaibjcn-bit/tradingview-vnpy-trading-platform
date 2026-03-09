"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Shield,
  ShieldAlert,
  Lock,
  AlertTriangle,
  Power,
  RefreshCw,
  History,
  Key,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface SettingsClientProps {
  userId: string;
}

interface LogEntry {
  id: string;
  operation: string;
  details: Record<string, unknown>;
  timestamp: string;
  success: boolean;
}

export function SettingsClient({ userId }: SettingsClientProps) {
  const [activeTab, setActiveTab] = useState<"security" | "logs">("security");
  const [emergencyStop, setEmergencyStop] = useState(false);
  const [emergencyReason, setEmergencyReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [tradePassword, setTradePassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState<string | false>(false);
  const [pendingOperation, setPendingOperation] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Password confirmation handler
  const handlePasswordConfirmed = async () => {
    if (!pendingOperation) return;

    setLoading(true);
    try {
      const res = await fetch("/api/security", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          action: pendingOperation,
          password: tradePassword,
        }),
      });

      const data = await res.json();
      if (data.status === "ok" || data.confirmed) {
        if (pendingOperation === "reset_emergency_stop") {
          setEmergencyStop(false);
          setMessage({ type: "success", text: "紧急停止已解除" });
        }
        setShowPasswordConfirm(false);
        setPendingOperation(null);
        setTradePassword("");
      } else {
        setMessage({ type: "error", text: data.message || "操作失败" });
      }
    } catch {
      setMessage({ type: "error", text: "操作失败" });
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/security?action=status");
      if (res.ok) {
        const data = await res.json();
        setEmergencyStop(data.emergencyStop);
      }
    } catch (error) {
      console.error("Failed to fetch status:", error);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch("/api/security?action=logs");
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  useEffect(() => {
    if (activeTab === "logs") {
      fetchLogs();
    }
  }, [activeTab, fetchLogs]);

  const handleEmergencyStop = async () => {
    if (!confirm("确定要触发紧急停止吗？这将停止所有自动交易。")) return;

    setLoading(true);
    try {
      const res = await fetch("/api/security", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          action: "emergency_stop",
          reason: emergencyReason || "手动触发",
        }),
      });

      const data = await res.json();
      if (data.status === "ok") {
        setEmergencyStop(true);
        setMessage({ type: "success", text: "紧急停止已激活" });
      } else {
        setMessage({ type: "error", text: data.message || "操作失败" });
      }
    } catch {
      setMessage({ type: "error", text: "操作失败" });
    } finally {
      setLoading(false);
    }
  };

  const handleResetEmergencyStop = () => {
    setPendingOperation("reset_emergency_stop");
    setShowPasswordConfirm("reset_emergency_stop");
  };

  const handleSetPassword = async () => {
    if (tradePassword !== confirmPassword) {
      setMessage({ type: "error", text: "两次输入的密码不一致" });
      return;
    }

    if (tradePassword.length < 6) {
      setMessage({ type: "error", text: "密码长度至少为6位" });
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/security", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          action: "set_password",
          newPassword: tradePassword,
        }),
      });

      const data = await res.json();
      if (data.status === "ok") {
        setMessage({ type: "success", text: "交易密码已设置" });
        setTradePassword("");
        setConfirmPassword("");
      } else {
        setMessage({ type: "error", text: data.message || "设置失败" });
      }
    } catch {
      setMessage({ type: "error", text: "设置失败" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">系统设置</h1>
          <p className="text-sm text-zinc-500 mt-1">安全配置和系统控制</p>
        </div>
        <button
          onClick={fetchStatus}
          className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === "success"
            ? "bg-green-500/20 text-green-300 border border-green-500/30"
            : "bg-red-500/20 text-red-300 border border-red-500/30"
        }`}>
          <div className="flex items-center gap-2">
            {message.type === "success" ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <XCircle className="h-5 w-5" />
            )}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Emergency Stop Banner */}
      {emergencyStop && (
        <div className="border border-red-500/50 bg-red-500/10 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-500/20 rounded-full">
              <ShieldAlert className="h-8 w-8 text-red-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-400">紧急停止已激活</h3>
              <p className="text-sm text-red-300 mt-1">
                所有自动交易已暂停。解除需要输入交易密码。
              </p>
            </div>
            <button
              onClick={handleResetEmergencyStop}
              className="px-4 py-2 bg-red-500 hover:bg-red-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Power className="h-4 w-4" />
              解除停止
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        <button
          onClick={() => setActiveTab("security")}
          className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
            activeTab === "security"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <Shield className="h-4 w-4" />
          安全设置
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
            activeTab === "logs"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <History className="h-4 w-4" />
          操作日志
        </button>
      </div>

      {/* Security Settings Tab */}
      {activeTab === "security" && (
        <div className="space-y-6">
          {/* Emergency Stop */}
          <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
            <div className="flex items-center gap-3 mb-4">
              <ShieldAlert className="h-5 w-5 text-red-400" />
              <h3 className="text-lg font-semibold text-zinc-100">紧急停止</h3>
            </div>
            <p className="text-sm text-zinc-400 mb-4">
              立即停止所有自动交易策略。在市场异常或发现问题时使用。
            </p>

            <div className="flex items-center gap-4">
              <input
                type="text"
                value={emergencyReason}
                onChange={(e) => setEmergencyReason(e.target.value)}
                placeholder="停止原因（可选）"
                className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                disabled={emergencyStop}
              />
              <button
                onClick={handleEmergencyStop}
                disabled={emergencyStop || loading}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {loading ? <Spinner size="sm" /> : <><Power className="h-4 w-4" /> 紧急停止</>}
              </button>
            </div>
          </div>

          {/* Trading Password */}
          <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
            <div className="flex items-center gap-3 mb-4">
              <Key className="h-5 w-5 text-yellow-400" />
              <h3 className="text-lg font-semibold text-zinc-100">交易密码</h3>
            </div>
            <p className="text-sm text-zinc-400 mb-4">
              设置交易密码用于确认敏感操作（如大额交易、解除紧急停止等）。
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-500 mb-2">新密码</label>
                <input
                  type="password"
                  value={tradePassword}
                  onChange={(e) => setTradePassword(e.target.value)}
                  placeholder="至少6位字符"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-500 mb-2">确认密码</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="再次输入密码"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              </div>
              <button
                onClick={handleSetPassword}
                disabled={loading}
                className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {loading ? <Spinner size="sm" /> : <><Lock className="h-4 w-4" /> 设置密码</>}
              </button>
            </div>
          </div>

          {/* Security Info */}
          <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="h-5 w-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-zinc-100">安全提示</h3>
            </div>
            <ul className="space-y-2 text-sm text-zinc-400">
              <li className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>交易密码不同于登录密码，用于确认所有交易相关操作</span>
              </li>
              <li className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>所有敏感操作都会被记录在操作日志中</span>
              </li>
              <li className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>策略沙箱模式可安全测试策略而不产生实际交易</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === "logs" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-zinc-100">操作日志</h3>
            <button
              onClick={fetchLogs}
              className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800 bg-zinc-900">
                  <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase">时间</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase">操作</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase">详情</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase">状态</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center py-8 text-zinc-500">
                      暂无操作日志
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {new Date(log.timestamp).toLocaleString("zh-CN")}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-300">{log.operation}</td>
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {JSON.stringify(log.details)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          log.success
                            ? "bg-green-500/20 text-green-400"
                            : "bg-red-500/20 text-red-400"
                        }`}>
                          {log.success ? "成功" : "失败"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Password Confirmation Modal */}
      {showPasswordConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-900 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-zinc-100 mb-4">确认操作</h3>
            <p className="text-sm text-zinc-400 mb-4">
              {pendingOperation === "reset_emergency_stop"
                ? "解除紧急停止需要输入交易密码确认"
                : "请输入交易密码确认此操作"}
            </p>
            <input
              type="password"
              value={tradePassword}
              onChange={(e) => setTradePassword(e.target.value)}
              placeholder="交易密码"
              autoFocus
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowPasswordConfirm(false);
                  setTradePassword("");
                }}
                className="flex-1 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg font-medium transition-colors"
              >
                取消
              </button>
              <button
                onClick={handlePasswordConfirmed}
                disabled={loading || !tradePassword}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? <Spinner size="sm" /> : "确认"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
