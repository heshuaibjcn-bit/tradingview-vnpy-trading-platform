"use client";

import { useState, useCallback, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { Order } from "@/types/database";
import { QuickTradeForm } from "./QuickTradeForm";
import { ClearAllPositions } from "./ClearAllPositions";
import { BatchOrderForm } from "./BatchOrderForm";

interface TradeClientProps {
  userId: string;
}

export function TradeClient({ userId }: TradeClientProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const refreshData = useCallback(async () => {
    try {
      setLoading(true);
      const ordersRes = await fetch(`/api/dashboard/orders?userId=${userId}`);

      if (ordersRes.ok) {
        const ordersData = await ordersRes.json();
        setOrders(ordersData.orders || []);
      }
    } catch (error) {
      console.error("Failed to refresh trade data:", error);
    } finally {
      setLoading(false);
      setLastUpdate(new Date());
    }
  }, [userId]);

  useEffect(() => {
    refreshData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(refreshData, 5000);
    return () => clearInterval(interval);
  }, [refreshData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">手动交易</h1>
          <p className="text-sm text-zinc-500 mt-1">快速下单和仓位管理</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={refreshData}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
            title="刷新"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <span className="text-xs text-zinc-600">
            最后更新: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Quick Trade */}
        <div>
          <QuickTradeForm userId={userId} />
        </div>

        {/* Right Column - Tools */}
        <div className="space-y-6">
          {/* Clear All Positions */}
          <div>
            <h3 className="text-sm font-medium text-zinc-400 mb-3">仓位管理</h3>
            <ClearAllPositions userId={userId} onCleared={refreshData} />
          </div>

          {/* Batch Orders */}
          <div>
            <h3 className="text-sm font-medium text-zinc-400 mb-3">批量交易</h3>
            <BatchOrderForm userId={userId} />
          </div>
        </div>
      </div>

      {/* Today's Orders */}
      <div>
        <h3 className="text-sm font-medium text-zinc-400 mb-3">
          今日委托
        </h3>
        <div className="border border-zinc-800 rounded-lg overflow-hidden">
          {orders.length === 0 ? (
            <div className="p-8 text-center text-zinc-500">
              今日暂无委托记录
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-800 text-zinc-400">
                  <tr>
                    <th className="px-4 py-3 text-left">时间</th>
                    <th className="px-4 py-3 text-left">股票</th>
                    <th className="px-4 py-3 text-left">方向</th>
                    <th className="px-4 py-3 text-right">价格</th>
                    <th className="px-4 py-3 text-right">数量</th>
                    <th className="px-4 py-3 text-center">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id} className="border-t border-zinc-800">
                      <td className="px-4 py-3 text-zinc-500">
                        {new Date(order.created_at).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 font-mono text-zinc-200">
                        {order.symbol}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={
                            order.side === "buy"
                              ? "text-red-400"
                              : "text-green-400"
                          }
                        >
                          {order.side === "buy" ? "买入" : "卖出"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        ¥{order.price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        {order.quantity}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            order.status === "filled"
                              ? "bg-green-500/20 text-green-400"
                              : order.status === "cancelled"
                              ? "bg-zinc-700 text-zinc-500"
                              : order.status === "failed"
                              ? "bg-red-500/20 text-red-400"
                              : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {order.status === "filled"
                            ? "已成交"
                            : order.status === "cancelled"
                            ? "已撤销"
                            : order.status === "failed"
                            ? "失败"
                            : order.status === "partial_filled"
                            ? "部分成交"
                            : "待提交"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
