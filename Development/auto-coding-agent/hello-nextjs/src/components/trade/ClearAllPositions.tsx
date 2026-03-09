"use client";

import { useState, useCallback } from "react";
import { AlertTriangle, X, Trash2 } from "lucide-react";
import { Position } from "@/types/database";
import { Spinner } from "@/components/ui/Spinner";

interface ClearAllPositionsProps {
  userId: string;
  onCleared?: () => void;
}

export function ClearAllPositions({ userId, onCleared }: ClearAllPositionsProps) {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [step, setStep] = useState<"idle" | "confirm" | "password">("idle");

  // Fetch positions
  const fetchPositions = useCallback(async () => {
    try {
      const res = await fetch(`/api/dashboard/positions?userId=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setPositions(data.positions || []);
      }
    } catch (error) {
      console.error("Failed to fetch positions:", error);
    }
  }, [userId]);

  // Open confirm dialog
  const handleOpen = () => {
    if (positions.length === 0) {
      alert("当前没有持仓");
      return;
    }
    setStep("confirm");
    setConfirmOpen(true);
    fetchPositions();
  };

  const handleClearAll = async () => {
    setLoading(true);

    try {
      // Submit sell orders for all positions
      const orders = positions.map((pos) =>
        fetch("/api/trade/order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userId,
            symbol: pos.symbol,
            side: "sell",
            orderType: "market",
            quantity: pos.quantity,
          }),
        })
      );

      const results = await Promise.allSettled(orders);

      const successCount = results.filter(
        (r): r is PromiseFulfilledResult<Response> =>
          r.status === "fulfilled" && r.value.ok
      ).length;
      const failCount = results.length - successCount;

      if (failCount > 0) {
        alert(`清仓完成: ${successCount}个成功, ${failCount}个失败`);
      } else {
        alert("清仓成功！所有持仓已市价卖出");
      }

      setConfirmOpen(false);
      setStep("idle");
      if (onCleared) onCleared();
    } catch (error) {
      console.error("Failed to clear positions:", error);
      alert("清仓失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const totalValue = positions.reduce((sum, pos) => {
    const currentValue = pos.current_price ?? pos.cost_price;
    return sum + currentValue * pos.quantity;
  }, 0);

  const totalProfit = positions.reduce((sum, pos) => {
    return sum + (pos.profit_loss || 0);
  }, 0);

  if (!confirmOpen) {
    return (
      <button
        onClick={handleOpen}
        className="w-full py-3 border border-red-900/50 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        <Trash2 className="h-4 w-4" />
        一键清仓
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            确认清仓
          </h3>
          <button
            onClick={() => {
              setConfirmOpen(false);
              setStep("idle");
            }}
            className="text-zinc-500 hover:text-zinc-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {step === "confirm" && (
          <>
            <div className="space-y-4">
              {/* Position Summary */}
              <div className="p-4 bg-zinc-800 rounded-lg">
                <p className="text-sm text-zinc-500 mb-3">
                  您即将卖出以下 {positions.length} 只股票:
                </p>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {positions.map((pos) => {
                    const currentValue = pos.current_price ?? pos.cost_price;
                    const posValue = currentValue * pos.quantity;
                    const pl = pos.profit_loss || 0;
                    const plPercent = pos.profit_loss_ratio || 0;

                    return (
                      <div
                        key={pos.id}
                        className="flex justify-between items-center py-2 border-b border-zinc-700 last:border-0"
                      >
                        <div>
                          <span className="font-mono text-zinc-200">{pos.symbol}</span>
                          <span className="text-zinc-500 text-sm ml-2">
                            {pos.quantity}股
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-zinc-300">
                            ¥{posValue.toFixed(2)}
                          </p>
                          <p className={`text-xs ${pl >= 0 ? "text-green-400" : "text-red-400"}`}>
                            {pl >= 0 ? "+" : ""}{pl.toFixed(2)} ({plPercent >= 0 ? "+" : ""}{plPercent.toFixed(2)}%)
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Summary */}
              <div className="flex justify-between py-2 border-t border-zinc-800">
                <span className="text-zinc-500">总市值:</span>
                <span className="font-mono text-zinc-200">¥{totalValue.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-zinc-500">总盈亏:</span>
                <span className={`font-mono ${totalProfit >= 0 ? "text-green-400" : "text-red-400"}`}>
                  {totalProfit >= 0 ? "+" : ""}¥{totalProfit.toFixed(2)}
                </span>
              </div>

              {/* Warning */}
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <p className="text-sm text-red-400">
                  ⚠️ 此操作将以市价卖出所有持仓，无法撤销
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setConfirmOpen(false);
                    setStep("idle");
                  }}
                  className="flex-1 py-2 px-4 border border-zinc-700 text-zinc-400 rounded-lg hover:bg-zinc-800 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleClearAll}
                  disabled={loading}
                  className="flex-1 py-2 px-4 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors disabled:bg-zinc-800 disabled:text-zinc-600"
                >
                  {loading ? <Spinner size="sm" /> : "确认清仓"}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
