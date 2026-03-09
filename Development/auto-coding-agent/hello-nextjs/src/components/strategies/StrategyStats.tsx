"use client";

import { Strategy, StrategySignal } from "@/types/database";

interface StrategyStatsProps {
  strategies: (Strategy & { signals?: StrategySignal[] })[];
}

export function StrategyStats({ strategies }: StrategyStatsProps) {
  // Calculate statistics
  const totalStrategies = strategies.length;
  const enabledStrategies = strategies.filter((s) => s.enabled).length;

  const allSignals = strategies.flatMap((s) => s.signals || []);
  const buySignals = allSignals.filter((s) => s.signal_type === "BUY").length;
  const sellSignals = allSignals.filter((s) => s.signal_type === "SELL").length;
  const pendingSignals = allSignals.filter((s) => !s.executed).length;

  const todaySignals = allSignals.filter((s) => {
    const signalDate = new Date(s.created_at).toDateString();
    const today = new Date().toDateString();
    return signalDate === today;
  }).length;

  const stats = [
    {
      label: "总策略数",
      value: totalStrategies,
      color: "text-zinc-300",
      bgColor: "bg-zinc-800/50",
    },
    {
      label: "运行中",
      value: enabledStrategies,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
    {
      label: "今日信号",
      value: todaySignals,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "待执行",
      value: pendingSignals,
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10",
    },
    {
      label: "买入信号",
      value: buySignals,
      color: "text-red-400",
      bgColor: "bg-red-500/10",
    },
    {
      label: "卖出信号",
      value: sellSignals,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`${stat.bgColor} border border-zinc-800 rounded-lg p-4`}
        >
          <p className="text-xs text-zinc-500 mb-1">{stat.label}</p>
          <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
