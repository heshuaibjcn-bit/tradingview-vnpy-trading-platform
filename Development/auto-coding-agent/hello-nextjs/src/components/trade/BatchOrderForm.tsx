"use client";

import { useState } from "react";
import { Plus, X, Check, Trash2 } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface BatchOrderFormProps {
  userId: string;
}

interface BatchOrder {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  orderType: "limit" | "market";
  price: string;
  quantity: string;
}

const emptyOrder: BatchOrder = {
  id: crypto.randomUUID(),
  symbol: "",
  side: "buy",
  orderType: "limit",
  price: "",
  quantity: "",
};

export function BatchOrderForm({ userId }: BatchOrderFormProps) {
  const [orders, setOrders] = useState<BatchOrder[]>([emptyOrder]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const addOrder = () => {
    setOrders([...orders, { ...emptyOrder, id: crypto.randomUUID() }]);
  };

  const removeOrder = (id: string) => {
    setOrders(orders.filter((o) => o.id !== id));
  };

  const updateOrder = (id: string, field: keyof BatchOrder, value: string) => {
    setOrders(
      orders.map((o) =>
        o.id === id ? { ...o, [field]: value } : o
      )
    );
  };

  const calculateTotal = () => {
    return orders.reduce((sum, order) => {
      const qty = parseInt(order.quantity) || 0;
      const pr = parseFloat(order.price) || 0;
      return order.orderType === "limit" ? sum + pr * qty : sum;
    }, 0);
  };

  const handleSubmit = async () => {
    const validOrders = orders.filter(
      (o) => o.symbol && o.quantity && (o.orderType === "market" || o.price)
    );

    if (validOrders.length === 0) {
      alert("请填写至少一个有效的订单");
      return;
    }

    setLoading(true);

    try {
      const results = await Promise.all(
        validOrders.map((order) =>
          fetch("/api/trade/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              userId,
              symbol: order.symbol.toUpperCase(),
              side: order.side,
              orderType: order.orderType,
              price: order.orderType === "limit" ? parseFloat(order.price) : null,
              quantity: parseInt(order.quantity),
            }),
          })
        )
      );

      const successCount = results.filter((r) => r.ok).length;

      if (successCount === validOrders.length) {
        alert(`批量下单成功！已提交 ${successCount} 个订单`);
        setOrders([emptyOrder]);
        setIsOpen(false);
      } else {
        alert(`批量下单部分完成: ${successCount}/${validOrders.length} 个成功`);
      }
    } catch (error) {
      console.error("Failed to submit batch orders:", error);
      alert("批量下单失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full py-3 border border-zinc-700 rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="h-4 w-4" />
        批量下单
      </button>
    );
  }

  return (
    <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-900/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-100">批量下单</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-zinc-500 hover:text-zinc-300"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Order List */}
      <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
        {orders.map((order) => (
          <div
            key={order.id}
            className="p-4 bg-zinc-800 rounded-lg border border-zinc-700"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 grid grid-cols-2 gap-3">
                {/* Symbol */}
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">股票代码</label>
                  <input
                    type="text"
                    value={order.symbol}
                    onChange={(e) => updateOrder(order.id, "symbol", e.target.value.toUpperCase())}
                    placeholder="600519"
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 text-sm focus:outline-none focus:border-zinc-600"
                  />
                </div>

                {/* Side */}
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">方向</label>
                  <select
                    value={order.side}
                    onChange={(e) => updateOrder(order.id, "side", e.target.value as "buy" | "sell")}
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 text-sm focus:outline-none focus:border-zinc-600"
                  >
                    <option value="buy">买入</option>
                    <option value="sell">卖出</option>
                  </select>
                </div>

                {/* Order Type */}
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">类型</label>
                  <select
                    value={order.orderType}
                    onChange={(e) => updateOrder(order.id, "orderType", e.target.value as "limit" | "market")}
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 text-sm focus:outline-none focus:border-zinc-600"
                  >
                    <option value="limit">限价</option>
                    <option value="market">市价</option>
                  </select>
                </div>

                {/* Price */}
                {order.orderType === "limit" && (
                  <div>
                    <label className="block text-xs text-zinc-500 mb-1">价格</label>
                    <input
                      type="number"
                      step="0.01"
                      value={order.price}
                      onChange={(e) => updateOrder(order.id, "price", e.target.value)}
                      placeholder="价格"
                      className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 text-sm focus:outline-none focus:border-zinc-600"
                    />
                  </div>
                )}

                {/* Quantity */}
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">数量</label>
                  <input
                    type="number"
                    value={order.quantity}
                    onChange={(e) => updateOrder(order.id, "quantity", e.target.value)}
                    placeholder="100"
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-200 text-sm focus:outline-none focus:border-zinc-600"
                  />
                </div>
              </div>

              {/* Remove Button */}
              <button
                onClick={() => removeOrder(order.id)}
                className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg"
                title="删除"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>

            {/* Order Amount */}
            {order.orderType === "limit" && order.price && order.quantity && (
              <div className="mt-2 pt-2 border-t border-zinc-700 text-sm text-zinc-500">
                金额: ¥{((parseFloat(order.price) || 0) * (parseInt(order.quantity) || 0)).toFixed(2)}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Order Button */}
      <button
        onClick={addOrder}
        className="w-full py-2 border border-dashed border-zinc-700 text-zinc-500 hover:border-zinc-600 hover:text-zinc-400 rounded-lg flex items-center justify-center gap-2 mb-4"
      >
        <Plus className="h-4 w-4" />
        添加订单
      </button>

      {/* Total Summary */}
      <div className="flex justify-between py-3 px-4 bg-zinc-800 rounded-lg mb-4">
        <span className="text-zinc-500">预计总金额:</span>
        <span className="font-mono text-zinc-200">¥{calculateTotal().toFixed(2)}</span>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
      >
        {loading ? <Spinner size="sm" /> : <><Check className="h-4 w-4" /> 提交批量订单</>}
      </button>
    </div>
  );
}
