import type { Order } from "@/types/database";
import { Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface OrderListProps {
  orders: Order[];
  onUpdate?: () => void;
}

const orderStatusConfig = {
  pending: {
    label: "待提交",
    icon: Clock,
    className: "text-zinc-500",
    bgClassName: "bg-zinc-100 dark:bg-zinc-800",
  },
  submitted: {
    label: "已提交",
    icon: Loader2,
    className: "text-blue-500",
    bgClassName: "bg-blue-100 dark:bg-blue-900/30",
  },
  partial_filled: {
    label: "部分成交",
    icon: Clock,
    className: "text-yellow-500",
    bgClassName: "bg-yellow-100 dark:bg-yellow-900/30",
  },
  filled: {
    label: "已成交",
    icon: CheckCircle2,
    className: "text-green-500",
    bgClassName: "bg-green-100 dark:bg-green-900/30",
  },
  cancelled: {
    label: "已撤单",
    icon: XCircle,
    className: "text-red-500",
    bgClassName: "bg-red-100 dark:bg-red-900/30",
  },
  failed: {
    label: "失败",
    icon: XCircle,
    className: "text-red-500",
    bgClassName: "bg-red-100 dark:bg-red-900/30",
  },
};

export function OrderList({ orders, onUpdate }: OrderListProps) {
  if (orders.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">今日委托</h2>
        <div className="text-center text-zinc-500 dark:text-zinc-400">
          <p>今日暂无委托</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          今日委托 ({orders.length})
        </h2>
        <div className="flex gap-2">
          <button
            onClick={onUpdate}
            className="rounded px-3 py-1 text-sm text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            刷新
          </button>
        </div>
      </div>

      <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
        {orders.slice(0, 10).map((order) => {
          const statusConfig = orderStatusConfig[order.status];
          const StatusIcon = statusConfig.icon;
          const isBuy = order.side === "buy";

          return (
            <div key={order.id} className="flex items-center justify-between p-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <div className={`rounded-full px-2 py-1 text-xs font-medium ${
                    isBuy ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" : "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                  }`}>
                    {isBuy ? "买入" : "卖出"}
                  </div>
                  <div>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                      {order.symbol}
                    </p>
                    <p className="text-sm text-zinc-500">
                      {new Date(order.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm text-zinc-500">
                    {order.quantity}股 @ ¥{order.price.toFixed(2)}
                  </p>
                  {order.filled_quantity > 0 && (
                    <p className="text-sm text-zinc-500">
                      成交: {order.filled_quantity}股
                      {order.filled_price && ` @ ¥${order.filled_price.toFixed(2)}`}
                    </p>
                  )}
                </div>

                <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 ${statusConfig.className} ${statusConfig.bgClassName}`}>
                  <StatusIcon className="h-3.5 w-3.5" />
                  <span className="text-xs font-medium">{statusConfig.label}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {orders.length > 10 && (
        <div className="border-t border-zinc-200 p-3 text-center dark:border-zinc-800">
          <p className="text-sm text-zinc-500">
            还有 {orders.length - 10} 条委托记录...
          </p>
        </div>
      )}
    </div>
  );
}
