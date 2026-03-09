"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Bell,
  Plus,
  Trash2,
  Check,
  X,
  TrendingUp,
  TrendingDown,
  Activity,
  Volume2,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

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
  symbol: string;
  alertType: string;
  message: string;
  value: number;
  threshold: number;
  triggeredAt: string;
  acknowledged: boolean;
}

interface AlertsClientProps {
  userId: string;
}

const ALERT_TYPE_INFO: Record<string, { icon: React.ComponentType<{ className?: string }>; label: string; color: string }> = {
  price_above: { icon: TrendingUp, label: "价格上限", color: "text-green-400" },
  price_below: { icon: TrendingDown, label: "价格下限", color: "text-red-400" },
  price_change: { icon: Activity, label: "价格异动", color: "text-yellow-400" },
  volume_spike: { icon: Volume2, label: "成交量", color: "text-blue-400" },
  rsi_overbought: { icon: TrendingUp, label: "RSI超买", color: "text-orange-400" },
  rsi_oversold: { icon: TrendingDown, label: "RSI超卖", color: "text-purple-400" },
};

export function AlertsClient({ userId }: AlertsClientProps) {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [alerts, setAlerts] = useState<AlertHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedTab, setSelectedTab] = useState<"rules" | "history">("rules");

  // New rule form state
  const [newRule, setNewRule] = useState({
    symbol: "600519",
    alertType: "price_above",
    threshold: 100,
    name: "",
    description: "",
  });

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesRes, alertsRes] = await Promise.all([
        fetch(`/api/alerts?userId=${userId}`),
        fetch(`/api/alerts?userId=${userId}&action=history`),
      ]);

      if (rulesRes.ok) {
        const data = await rulesRes.json();
        setRules(data.rules || []);
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchAlerts();
    // Refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const handleCreateRule = async () => {
    try {
      const res = await fetch("/api/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "create",
          userId,
          ...newRule,
        }),
      });

      if (res.ok) {
        setShowCreateForm(false);
        setNewRule({
          symbol: "600519",
          alertType: "price_above",
          threshold: 100,
          name: "",
          description: "",
        });
        fetchAlerts();
      }
    } catch (error) {
      console.error("Failed to create rule:", error);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("确定要删除这条告警规则吗？")) {
      return;
    }

    try {
      const res = await fetch(`/api/alerts?ruleId=${ruleId}`, {
        method: "DELETE",
      });

      if (res.ok) {
        fetchAlerts();
      }
    } catch (error) {
      console.error("Failed to delete rule:", error);
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      const res = await fetch("/api/alerts", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ruleId,
          userId,
          enabled,
        }),
      });

      if (res.ok) {
        fetchAlerts();
      }
    } catch (error) {
      console.error("Failed to toggle rule:", error);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    setAlerts(alerts.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">行情监控</h1>
          <p className="text-sm text-zinc-500 mt-1">设置价格和成交量告警</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <Plus className="h-4 w-4" /> 新建告警
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        <button
          onClick={() => setSelectedTab("rules")}
          className={`px-4 py-2 font-medium transition-colors ${
            selectedTab === "rules"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          告警规则 ({rules.length})
        </button>
        <button
          onClick={() => setSelectedTab("history")}
          className={`px-4 py-2 font-medium transition-colors ${
            selectedTab === "history"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          告警历史 ({alerts.length})
        </button>
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-zinc-100">新建告警规则</h3>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-zinc-500 hover:text-zinc-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  股票代码
                </label>
                <input
                  type="text"
                  value={newRule.symbol}
                  onChange={(e) => setNewRule({ ...newRule, symbol: e.target.value.toUpperCase() })}
                  placeholder="600519"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  告警类型
                </label>
                <select
                  value={newRule.alertType}
                  onChange={(e) => setNewRule({ ...newRule, alertType: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                >
                  {Object.entries(ALERT_TYPE_INFO).map(([key, info]) => (
                    <option key={key} value={key}>
                      {info.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  阈值
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={newRule.threshold}
                  onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) })}
                  placeholder="价格阈值"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  规则名称（可选）
                </label>
                <input
                  type="text"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="例如：茅台价格突破1000"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  描述（可选）
                </label>
                <input
                  type="text"
                  value={newRule.description}
                  onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                  placeholder="规则描述"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 py-2 border border-zinc-700 text-zinc-400 rounded-lg hover:bg-zinc-800 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateRule}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rules Tab */}
      {selectedTab === "rules" && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : rules.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-zinc-800 rounded-lg">
              <Bell className="h-12 w-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">暂无告警规则</p>
              <p className="text-sm text-zinc-600 mt-1">点击上方&quot;新建告警&quot;添加第一条规则</p>
            </div>
          ) : (
            rules.map((rule) => {
              const info = ALERT_TYPE_INFO[rule.alertType] || ALERT_TYPE_INFO.price_above;
              const Icon = info.icon;

              return (
                <div
                  key={rule.id}
                  className={`border rounded-lg p-4 transition-colors ${
                    rule.enabled
                      ? "border-zinc-800 bg-zinc-900/50"
                      : "border-zinc-800 bg-zinc-900/20 opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${info.color} bg-opacity-20`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-zinc-200">
                          {rule.name || rule.symbol}
                        </h3>
                        <p className="text-sm text-zinc-500 mt-1">
                          {rule.description || info.label}
                        </p>
                        <div className="flex gap-4 mt-2 text-sm">
                          <span className="text-zinc-600">代码: {rule.symbol}</span>
                          <span className="text-zinc-600">阈值: {rule.threshold}</span>
                          <span className={`text-zinc-600 ${rule.enabled ? "text-green-500" : "text-red-500"}`}>
                            {rule.enabled ? "已启用" : "已禁用"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleRule(rule.id, !rule.enabled)}
                        className={`p-2 rounded-lg transition-colors ${
                          rule.enabled
                            ? "bg-green-500/20 text-green-400 hover:bg-green-500/30"
                            : "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        }`}
                        title={rule.enabled ? "禁用" : "启用"}
                      >
                        {rule.enabled ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* History Tab */}
      {selectedTab === "history" && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-zinc-800 rounded-lg">
              <Bell className="h-12 w-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">暂无告警历史</p>
            </div>
          ) : (
            alerts.map((alert) => {
              const info = ALERT_TYPE_INFO[alert.alertType] || ALERT_TYPE_INFO.price_above;
              const Icon = info.icon;

              return (
                <div
                  key={alert.id}
                  className={`border border-zinc-800 rounded-lg p-4 transition-colors ${
                    alert.acknowledged ? "opacity-60" : ""
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${info.color} bg-opacity-20`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-zinc-200">{alert.symbol}</h3>
                        <p className="text-sm text-zinc-400 mt-1">{alert.message}</p>
                        <div className="flex gap-4 mt-2 text-sm">
                          <span className="text-zinc-600">
                            触发: {new Date(alert.triggeredAt).toLocaleString()}
                          </span>
                          <span className="text-zinc-600">
                            当前价: ¥{alert.value.toFixed(2)}
                          </span>
                          <span className="text-zinc-600">
                            阈值: ¥{alert.threshold.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded text-sm transition-colors"
                      >
                        标记已读
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
