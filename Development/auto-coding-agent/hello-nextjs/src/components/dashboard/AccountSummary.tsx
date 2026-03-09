import type { Position } from "@/types/database";
import { TrendingUp, TrendingDown, Wallet, PieChart } from "lucide-react";

interface AccountSummaryProps {
  positions: Position[];
}

export function AccountSummary({ positions }: AccountSummaryProps) {
  // Calculate totals
  let totalValue = 0;
  let totalCost = 0;
  let totalProfitLoss = 0;
  let totalProfitLossRatio = 0;

  for (const position of positions) {
    const currentValue = (position.current_price || position.cost_price) * position.quantity;
    totalValue += currentValue;
    totalCost += position.cost_price * position.quantity;
  }

  totalProfitLoss = totalValue - totalCost;
  totalProfitLossRatio = totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0;

  const isProfitable = totalProfitLoss >= 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* Total Assets */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-2 flex items-center text-zinc-500">
          <Wallet className="mr-2 h-5 w-5" />
          <span className="text-sm font-medium">总资产</span>
        </div>
        <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          ¥{totalValue.toFixed(2)}
        </div>
      </div>

      {/* Total Cost */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-2 flex items-center text-zinc-500">
          <PieChart className="mr-2 h-5 w-5" />
          <span className="text-sm font-medium">持仓成本</span>
        </div>
        <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          ¥{totalCost.toFixed(2)}
        </div>
      </div>

      {/* Profit/Loss */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-2 flex items-center text-zinc-500">
          {isProfitable ? (
            <TrendingUp className="mr-2 h-5 w-5 text-green-500" />
          ) : (
            <TrendingDown className="mr-2 h-5 w-5 text-red-500" />
          )}
          <span className="text-sm font-medium">总盈亏</span>
        </div>
        <div
          className={`text-2xl font-bold ${
            isProfitable ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          }`}
        >
          {isProfitable ? "+" : ""}¥{totalProfitLoss.toFixed(2)}
        </div>
      </div>

      {/* Profit/Loss Ratio */}
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-2 flex items-center text-zinc-500">
          {isProfitable ? (
            <TrendingUp className="mr-2 h-5 w-5 text-green-500" />
          ) : (
            <TrendingDown className="mr-2 h-5 w-5 text-red-500" />
          )}
          <span className="text-sm font-medium">盈亏比例</span>
        </div>
        <div
          className={`text-2xl font-bold ${
            isProfitable ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          }`}
        >
          {isProfitable ? "+" : ""}{totalProfitLossRatio.toFixed(2)}%
        </div>
      </div>
    </div>
  );
}
