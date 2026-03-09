import type { Position } from "@/types/database";
import { TrendingUp, TrendingDown, MoreHorizontal } from "lucide-react";

interface PositionListProps {
  positions: Position[];
  onUpdate?: () => void; // Reserved for future use
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function PositionList({ positions, onUpdate }: PositionListProps) {
  if (positions.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">持仓列表</h2>
        <div className="text-center text-zinc-500 dark:text-zinc-400">
          <p>暂无持仓</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          持仓列表 ({positions.length})
        </h2>
        <button className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300">
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </div>

      <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
        {positions.map((position) => {
          const currentValue = (position.current_price || position.cost_price) * position.quantity;
          const profitLoss = position.profit_loss ?? currentValue - position.cost_price * position.quantity;
          const profitLossRatio = position.profit_loss_ratio ?? (profitLoss / (position.cost_price * position.quantity)) * 100;
          const isProfitable = profitLoss >= 0;

          return (
            <div key={position.symbol} className="flex items-center justify-between p-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <div>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                      {position.symbol}
                    </p>
                    <p className="text-sm text-zinc-500">
                      {position.quantity}股 · 成本¥{position.cost_price.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm text-zinc-500">当前市值</p>
                  <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                    ¥{currentValue.toFixed(2)}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-zinc-500">盈亏</p>
                  <div className={`flex items-center gap-1 ${
                    isProfitable ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                  }`}>
                    {isProfitable ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    <span className="font-semibold">
                      {isProfitable ? "+" : ""}¥{profitLoss.toFixed(2)}
                    </span>
                  </div>
                  <p className={`text-sm ${
                    isProfitable ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                  }`}>
                    {isProfitable ? "+" : ""}{profitLossRatio.toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
