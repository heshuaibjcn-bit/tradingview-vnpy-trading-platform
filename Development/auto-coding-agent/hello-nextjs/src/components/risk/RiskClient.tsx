"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Shield,
  ShieldAlert,
  TrendingUp,
  AlertTriangle,
  Settings,
  Save,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface RiskClientProps {
  userId: string;
}

interface RiskConfig {
  maxPositionValue: number;
  maxPositionPct: number;
  maxTotalPositions: number;
  maxTotalExposure: number;
  stopLossEnabled: boolean;
  stopLossPct: number;
  takeProfitPct: number;
  maxDailyTrades: number;
  maxDailyLossPct: number;
}

interface RiskSummary {
  positionLimits: {
    maxPositionValue: number;
    maxPositionPct: string;
    maxTotalPositions: number;
    maxTotalExposure: string;
    currentExposure: string;
  };
  tradingLimits: {
    maxDailyTrades: number;
    tradesToday: number;
    maxDailyLoss: string;
    lossToday: string;
  };
  stopLoss: {
    enabled: boolean;
    stopLoss: string;
    takeProfit: string;
  };
}

const DEFAULT_CONFIG: RiskConfig = {
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

export function RiskClient({ userId }: RiskClientProps) {
  const [config, setConfig] = useState<RiskConfig>(DEFAULT_CONFIG);
  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "settings">("overview");

  const fetchRiskStatus = useCallback(async () => {
    try {
      const [configRes, summaryRes] = await Promise.all([
        fetch("/api/risk"),
        fetch("/api/risk?action=status"),
      ]);

      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(data.config);
      }

      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data.summary);
      }
    } catch (error) {
      console.error("Failed to fetch risk status:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRiskStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchRiskStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchRiskStatus]);

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      const res = await fetch("/api/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "update",
          userId,
          ...config,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        alert("风险配置已保存");
      }
    } catch (error) {
      console.error("Failed to save config:", error);
      alert("保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (value: string, max: string) => {
    const val = parseFloat(value);
    const maxValue = parseFloat(max);
    if (val >= maxValue * 0.9) return "text-red-400";
    if (val >= maxValue * 0.7) return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">风险控制</h1>
          <p className="text-sm text-zinc-500 mt-1">管理交易风险和仓位限制</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={fetchRiskStatus}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <Shield className="h-5 w-5" />
          </button>
          <span className="text-xs text-zinc-600">
            自动刷新
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "overview"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          风险概览
        </button>
        <button
          onClick={() => setActiveTab("settings")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "settings"
              ? "text-blue-400 border-b-2 border-blue-400"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          参数设置
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : summary && (
            <>
              {/* Position Limits */}
              <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="h-5 w-5 text-green-400" />
                  <h3 className="text-lg font-semibold text-zinc-100">仓位限制</h3>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <MetricCard
                    label="单股最大金额"
                    value={`¥${summary.positionLimits.maxPositionValue.toLocaleString()}`}
                    icon={<Shield className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="单股最大仓位"
                    value={summary.positionLimits.maxPositionPct}
                    icon={<TrendingUp className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="最大持仓数"
                    value={summary.positionLimits.maxTotalPositions.toString()}
                    icon={<Shield className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="当前总仓位"
                    value={summary.positionLimits.currentExposure}
                    color={getStatusColor(summary.positionLimits.currentExposure, summary.positionLimits.maxTotalExposure)}
                    icon={<TrendingUp className="h-4 w-4" />}
                  />
                </div>
              </div>

              {/* Trading Limits */}
              <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                <div className="flex items-center gap-3 mb-4">
                  <ShieldAlert className="h-5 w-5 text-yellow-400" />
                  <h3 className="text-lg font-semibold text-zinc-100">交易限制</h3>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <MetricCard
                    label="每日交易次数"
                    value={`${summary.tradingLimits.tradesToday}/${summary.tradingLimits.maxDailyTrades}`}
                    icon={<Activity className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="每日最大亏损"
                    value={summary.tradingLimits.maxDailyLoss}
                    icon={<TrendingUp className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="今日亏损"
                    value={summary.tradingLimits.lossToday}
                    color={parseFloat(summary.tradingLimits.lossToday) > 0 ? "text-red-400" : "text-green-400"}
                    icon={<TrendingUp className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="止损状态"
                    value={summary.stopLoss.enabled ? "已启用" : "已禁用"}
                    color={summary.stopLoss.enabled ? "text-green-400" : "text-zinc-500"}
                    icon={<Shield className="h-4 w-4" />}
                  />
                </div>
              </div>

              {/* Risk Warnings */}
              {(parseFloat(summary.tradingLimits.lossToday) > 0 ||
               parseFloat(summary.positionLimits.currentExposure) > 0.9) && (
                <div className="border border-yellow-500/20 bg-yellow-500/10 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-400" />
                    <h3 className="text-lg font-semibold text-yellow-400">风险提示</h3>
                  </div>
                  <p className="text-sm text-yellow-200 mt-2">
                    {parseFloat(summary.tradingLimits.lossToday) > 0
                      ? "今日已产生亏损，请注意控制风险"
                      : "当前仓位接近上限，建议谨慎开仓"}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === "settings" && (
        <div className="space-y-6">
          <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-zinc-400" />
                <h3 className="text-lg font-semibold text-zinc-100">风险参数设置</h3>
              </div>
              <button
                onClick={handleSaveConfig}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {saving ? <Spinner size="sm" /> : <><Save className="h-4 w-4" /> 保存配置</>}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Position Limits */}
              <div className="space-y-4">
                <h4 className="font-medium text-zinc-300">仓位限制</h4>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    单股最大金额 (元)
                  </label>
                  <input
                    type="number"
                    value={config.maxPositionValue}
                    onChange={(e) => setConfig({ ...config, maxPositionValue: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    单股最大仓位 (%)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    max="100"
                    value={config.maxPositionPct * 100}
                    onChange={(e) => setConfig({ ...config, maxPositionPct: parseFloat(e.target.value) / 100 })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    最大持仓数
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={config.maxTotalPositions}
                    onChange={(e) => setConfig({ ...config, maxTotalPositions: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    最大总仓位 (%)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    max="100"
                    value={config.maxTotalExposure * 100}
                    onChange={(e) => setConfig({ ...config, maxTotalExposure: parseFloat(e.target.value) / 100 })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                </div>
              </div>

              {/* Trading Limits */}
              <div className="space-y-4">
                <h4 className="font-medium text-zinc-300">交易限制</h4>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    每日最大交易次数
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="200"
                    value={config.maxDailyTrades}
                    onChange={(e) => setConfig({ ...config, maxDailyTrades: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    每日最大亏损 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="50"
                    value={config.maxDailyLossPct * 100}
                    onChange={(e) => setConfig({ ...config, maxDailyLossPct: parseFloat(e.target.value) / 100 })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                </div>
              </div>

              {/* Stop Loss Settings */}
              <div className="space-y-4 md:col-span-2">
                <h4 className="font-medium text-zinc-300">止损止盈</h4>

                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.stopLossEnabled}
                      onChange={(e) => setConfig({ ...config, stopLossEnabled: e.target.checked })}
                      className="rounded border-zinc-700"
                    />
                    <span className="text-sm text-zinc-400">启用止损止盈</span>
                  </label>
                </div>

                {config.stopLossEnabled && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-zinc-500 mb-2">
                        默认止损比例 (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="50"
                        value={config.stopLossPct * 100}
                        onChange={(e) => setConfig({ ...config, stopLossPct: parseFloat(e.target.value) / 100 })}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                      />
                    </div>

                    <div>
                      <label className="block text-sm text-zinc-500 mb-2">
                        默认止盈比例 (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="100"
                        value={config.takeProfitPct * 100}
                        onChange={(e) => setConfig({ ...config, takeProfitPct: parseFloat(e.target.value) / 100 })}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Risk Warning */}
          <div className="border border-red-900/50 bg-red-500/10 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-400">风险提示</h3>
                <p className="text-sm text-red-200 mt-1">
                  风险控制旨在降低交易风险，但不能完全避免损失。请根据自身情况合理设置参数。
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
}

function MetricCard({ label, value, icon, color }: MetricCardProps) {
  return (
    <div>
      <p className="text-sm text-zinc-500 flex items-center gap-2">
        {icon && <span className={color}>{icon}</span>}
        {label}
      </p>
      <p className={`text-xl font-semibold ${color || "text-zinc-200"}`}>
        {value}
      </p>
    </div>
  );
}

function Activity({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
