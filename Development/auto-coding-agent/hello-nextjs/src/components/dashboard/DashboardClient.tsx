"use client";

import { useCallback, useEffect, useState } from "react";
import { AccountSummary } from "./AccountSummary";
import { PositionList } from "./PositionList";
import { OrderList } from "./OrderList";
import { MarketWatch } from "./MarketWatch";
import type { Position, Order } from "@/types/database";

interface DashboardClientProps {
  userId: string;
}

export function DashboardClient({ userId }: DashboardClientProps) {
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [positionsRes, ordersRes] = await Promise.all([
        fetch(`/api/dashboard/positions?userId=${userId}`),
        fetch(`/api/dashboard/orders?userId=${userId}`),
      ]);

      if (positionsRes.ok && ordersRes.ok) {
        const [positionsData, ordersData] = await Promise.all([
          positionsRes.json(),
          ordersRes.json(),
        ]);
        setPositions(positionsData.positions || []);
        setOrders(ordersData.orders || []);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
      setLastUpdate(new Date());
    }
  }, [userId]);

  useEffect(() => {
    fetchDashboardData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  if (loading && positions.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-zinc-200 border-t-zinc-900 dark:border-zinc-800 dark:border-t-zinc-100" />
          <p className="text-sm text-zinc-600 dark:text-zinc-400">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Last update indicator */}
      <div className="flex items-center justify-end text-xs text-zinc-500">
        <span className="mr-1">最后更新:</span>
        <span>{lastUpdate.toLocaleTimeString()}</span>
        {loading && (
          <span className="ml-2 inline-block h-3 w-3 animate-pulse rounded-full bg-green-500" />
        )}
      </div>

      {/* Account Summary */}
      <AccountSummary positions={positions} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Positions */}
        <div className="lg:col-span-1">
          <PositionList positions={positions} onUpdate={fetchDashboardData} />
        </div>

        {/* Today's Orders */}
        <div className="lg:col-span-1">
          <OrderList orders={orders} onUpdate={fetchDashboardData} />
        </div>
      </div>

      {/* Market Watch */}
      <MarketWatch symbols={positions.map((p) => p.symbol)} />
    </div>
  );
}
