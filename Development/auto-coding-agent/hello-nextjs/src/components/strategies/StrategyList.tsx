"use client";

import { Play, Pause, Trash2, Signal, TrendingUp, TrendingDown } from "lucide-react";
import { useState, useCallback } from "react";
import type { Strategy, StrategySignal } from "@/types/database";
import { Spinner } from "@/components/ui/Spinner";

interface StrategyListProps {
  userId: string;
  initialStrategies: (Strategy & { signals?: StrategySignal[] })[];
}

const STRATEGY_TYPE_NAMES: Record<string, { name: string; description: string }> = {
  ma: { name: "均线策略", description: "基于移动平均线的金叉死叉信号" },
  macd: { name: "MACD策略", description: "基于MACD指标的趋势跟踪策略" },
  kdj: { name: "KDJ策略", description: "基于KDJ指标的超买超卖策略" },
  breakout: { name: "突破策略", description: "价格突破N日最高/最低点时交易" },
  grid: { name: "网格策略", description: "在指定价格区间内高抛低吸" },
};

export function StrategyList({ initialStrategies }: StrategyListProps) {
  const [strategies, setStrategies] = useState(initialStrategies);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleToggle = useCallback(async (id: string, enabled: boolean) => {
    try {
      setActionLoading(id);
      const res = await fetch(`/api/strategies/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: enabled ? "enable" : "disable" }),
      });

      if (res.ok) {
        const { strategy } = await res.json();
        setStrategies((prev) =>
          prev.map((s) => (s.id === id ? { ...s, ...strategy } : s))
        );
      }
    } catch (error) {
      console.error("Failed to toggle strategy:", error);
    } finally {
      setActionLoading(null);
    }
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm("确定要删除这个策略吗？")) return;

    try {
      setActionLoading(id);
      const res = await fetch(`/api/strategies/${id}`, { method: "DELETE" });

      if (res.ok) {
        setStrategies((prev) => prev.filter((s) => s.id !== id));
      }
    } catch (error) {
      console.error("Failed to delete strategy:", error);
    } finally {
      setActionLoading(null);
    }
  }, []);

  if (strategies.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-800 mb-4">
          <Signal className="w-8 h-8 text-zinc-600" />
        </div>
        <h3 className="text-lg font-medium text-zinc-300 mb-2">暂无策略</h3>
        <p className="text-zinc-500">点击下方按钮创建您的第一个交易策略</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {strategies.map((strategy) => {
        const typeInfo = STRATEGY_TYPE_NAMES[strategy.type] || { name: "未知策略", description: "" };
        const latestSignal = strategy.signals?.[0];
        const signalCount = strategy.signals?.length || 0;

        return (
          <div
            key={strategy.id}
            className={`rounded-lg border p-5 transition-colors ${
              strategy.enabled
                ? "border-zinc-700 bg-zinc-800/50"
                : "border-zinc-800 bg-zinc-900/30"
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg font-semibold text-zinc-100">
                    {strategy.name}
                  </h3>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      strategy.enabled
                        ? "bg-green-500/20 text-green-400"
                        : "bg-zinc-800 text-zinc-500"
                    }`}
                  >
                    {strategy.enabled ? "运行中" : "已停用"}
                  </span>
                  <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium text-zinc-400">
                    {typeInfo.name}
                  </span>
                </div>
                <p className="text-sm text-zinc-500">{typeInfo.description}</p>

                {/* Latest Signal */}
                {latestSignal && (
                  <div className="mt-3 flex items-center gap-3 p-3 bg-zinc-900/50 rounded-lg">
                    <div className="flex items-center gap-2">
                      {latestSignal.signal_type === "BUY" ? (
                        <TrendingUp className="h-4 w-4 text-red-500" />
                      ) : latestSignal.signal_type === "SELL" ? (
                        <TrendingDown className="h-4 w-4 text-green-500" />
                      ) : null}
                      <span className="text-sm text-zinc-300">
                        {latestSignal.symbol} {latestSignal.signal_type === "BUY" ? "买入" : "卖出"}
                      </span>
                    </div>
                    {latestSignal.price && (
                      <span className="text-sm font-mono text-zinc-400">
                        ¥{latestSignal.price.toFixed(2)}
                      </span>
                    )}
                    <span className="ml-auto text-xs text-zinc-600">
                      {new Date(latestSignal.created_at).toLocaleString()}
                    </span>
                  </div>
                )}

                {/* Parameters Display */}
                {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(strategy.parameters as Record<string, unknown>)
                      .filter(([key]) => key !== "symbols")
                      .map(([key, value]) => (
                        <span
                          key={key}
                          className="rounded bg-zinc-900 px-2 py-1 text-xs text-zinc-500"
                        >
                          {key}: {String(value)}
                        </span>
                      ))}
                  </div>
                )}

                {/* Signals Count */}
                <div className="mt-3 flex items-center gap-1 text-sm text-zinc-500">
                  <Signal className="h-3.5 w-3.5" />
                  <span>{signalCount} 个信号</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                {actionLoading === strategy.id ? (
                  <div className="p-2">
                    <Spinner size="sm" />
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleToggle(strategy.id, strategy.enabled)}
                      className={`rounded p-2 transition-colors ${
                        strategy.enabled
                          ? "text-green-400 hover:bg-green-500/10"
                          : "text-zinc-500 hover:bg-zinc-700 hover:text-zinc-300"
                      }`}
                      title={strategy.enabled ? "停用策略" : "启用策略"}
                    >
                      {strategy.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </button>
                    <button
                      onClick={() => handleDelete(strategy.id)}
                      className="rounded p-2 text-zinc-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
                      title="删除策略"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Strategy Symbols */}
            {(() => {
              const params = strategy.parameters as Record<string, unknown>;
              const symbols = params?.symbols;
              if (!symbols) return null;
              return (
                <div className="mt-3 pt-3 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500">
                    监控股票:{" "}
                    {Array.isArray(symbols) ? symbols.join(", ") : "全部"}
                  </p>
                </div>
              );
            })()}
          </div>
        );
      })}
    </div>
  );
}
