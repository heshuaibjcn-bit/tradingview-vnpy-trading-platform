"use client";

import { useState, useCallback, useEffect } from "react";
import { Strategy, StrategySignal } from "@/types/database";
import { StrategyList } from "./StrategyList";
import { CreateStrategyForm } from "./CreateStrategyForm";
import { StrategyStats } from "./StrategyStats";
import { Spinner } from "@/components/ui/Spinner";

interface StrategiesClientProps {
  userId: string;
  initialStrategies: (Strategy & { signals?: StrategySignal[] })[];
}

export function StrategiesClient({ userId, initialStrategies }: StrategiesClientProps) {
  const [strategies, setStrategies] = useState(initialStrategies);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const refreshStrategies = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/strategies?includeSignals=true&userId=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setStrategies(data.strategies || []);
      }
    } catch (error) {
      console.error("Failed to refresh strategies:", error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Auto-refresh every 10 seconds when enabled
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(refreshStrategies, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshStrategies]);

  const handleCreated = () => {
    refreshStrategies();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">策略管理</h1>
          <p className="text-sm text-zinc-500 mt-1">
            管理和监控您的交易策略
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-zinc-500">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-800 text-zinc-600 focus:ring-0"
            />
            自动刷新
          </label>
          {loading && <Spinner size="sm" />}
        </div>
      </div>

      {/* Stats */}
      <StrategyStats strategies={strategies} />

      {/* Strategy List */}
      <StrategyList userId={userId} initialStrategies={strategies} />

      {/* Create Form */}
      <CreateStrategyForm userId={userId} onCreated={handleCreated} />
    </div>
  );
}
