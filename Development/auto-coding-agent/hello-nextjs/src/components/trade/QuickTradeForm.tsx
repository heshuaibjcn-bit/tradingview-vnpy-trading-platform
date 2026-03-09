"use client";

import { useState, useEffect } from "react";
import { Position } from "@/types/database";
import { Spinner } from "@/components/ui/Spinner";

interface QuickTradeFormProps {
  userId: string;
  defaultSymbol?: string;
}

type OrderSide = "buy" | "sell";
type OrderType = "limit" | "market";

export function QuickTradeForm({ userId, defaultSymbol = "" }: QuickTradeFormProps) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [side, setSide] = useState<OrderSide>("buy");
  const [orderType, setOrderType] = useState<OrderType>("limit");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [positions, setPositions] = useState<Position[]>([]);
  const [latestPrice, setLatestPrice] = useState<number | null>(null);

  // Fetch positions for quantity reference
  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const res = await fetch(`/api/dashboard/positions?userId=${userId}`);
        if (res.ok) {
          const data = await res.json();
          setPositions(data.positions || []);
        }
      } catch (error) {
        console.error("Failed to fetch positions:", error);
      }
    };
    fetchPositions();
  }, [userId]);

  // Fetch latest price for symbol
  useEffect(() => {
    if (!symbol) return;

    const fetchPrice = async () => {
      try {
        // In a real app, this would come from market data API
        // For now, we'll use a placeholder
        const res = await fetch(`/api/market/quote?symbol=${symbol}`);
        if (res.ok) {
          const data = await res.json();
          setLatestPrice(data.price || null);
        }
      } catch {
        // Market API might not exist yet, that's ok
      }
    };
    fetchPrice();
  }, [symbol]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!symbol || !quantity) {
      alert("请输入股票代码和数量");
      return;
    }

    if (orderType === "limit" && !price) {
      alert("限价单必须输入价格");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/trade/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          symbol: symbol.toUpperCase(),
          side,
          orderType,
          price: orderType === "limit" ? parseFloat(price) : null,
          quantity: parseInt(quantity),
        }),
      });

      if (res.ok) {
        alert(`${side === "buy" ? "买入" : "卖出"}委托已提交`);
        // Reset form
        setSymbol("");
        setPrice("");
        setQuantity("");
        setLatestPrice(null);
      } else {
        const error = await res.json();
        alert(`下单失败: ${error.error || "未知错误"}`);
      }
    } catch (error) {
      console.error("Failed to submit order:", error);
      alert("下单失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const getPositionQuantity = (symbol: string) => {
    const pos = positions.find((p) => p.symbol.toUpperCase() === symbol.toUpperCase());
    return pos ? pos.quantity : 0;
  };

  const handleQuickSell = async () => {
    if (!symbol) {
      alert("请输入股票代码");
      return;
    }

    const availableQty = getPositionQuantity(symbol);
    if (availableQty === 0) {
      alert(`您没有 ${symbol} 的持仓`);
      return;
    }

    if (!confirm(`确定要卖出 ${symbol} ${availableQty} 股吗？`)) {
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/trade/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          symbol: symbol.toUpperCase(),
          side: "sell",
          orderType: "market",
          quantity: availableQty,
        }),
      });

      if (res.ok) {
        alert(`市价卖出委托已提交: ${symbol.toUpperCase()} ${availableQty}股`);
        setSymbol("");
        setLatestPrice(null);
      } else {
        const error = await res.json();
        alert(`卖出失败: ${error.error || "未知错误"}`);
      }
    } catch (error) {
      console.error("Failed to submit sell order:", error);
      alert("卖出失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Trade Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-100">快速交易</h2>
        <button
          onClick={() => {
            setSymbol("");
            setPrice("");
            setQuantity("");
            setLatestPrice(null);
          }}
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          重置
        </button>
      </div>

      {/* Side Selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setSide("buy")}
          className={`flex-1 py-3 rounded-lg font-medium transition-colors ${
            side === "buy"
              ? "bg-red-600 text-white"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
          }`}
        >
          买入
        </button>
        <button
          onClick={() => setSide("sell")}
          className={`flex-1 py-3 rounded-lg font-medium transition-colors ${
            side === "sell"
              ? "bg-green-600 text-white"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
          }`}
        >
          卖出
        </button>
      </div>

      {/* Trade Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Symbol Input */}
        <div>
          <label className="block text-sm font-medium text-zinc-400 mb-2">
            股票代码
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="例如: 600519"
            className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600 placeholder:text-zinc-600 font-mono"
          />
          {symbol && latestPrice && (
            <p className="text-sm text-zinc-500 mt-1">
              最新价: ¥{latestPrice.toFixed(2)}
            </p>
          )}
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-sm font-medium text-zinc-400 mb-2">
            订单类型
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setOrderType("limit")}
              className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                orderType === "limit"
                  ? "bg-zinc-700 text-zinc-200"
                  : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800"
              }`}
            >
              限价
            </button>
            <button
              type="button"
              onClick={() => setOrderType("market")}
              className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                orderType === "market"
                  ? "bg-zinc-700 text-zinc-200"
                  : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800"
              }`}
            >
              市价
            </button>
          </div>
        </div>

        {/* Price Input */}
        {orderType === "limit" && (
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              委托价格 (元)
            </label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="输入价格"
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600 placeholder:text-zinc-600 font-mono"
            />
          </div>
        )}

        {/* Quantity Input */}
        <div>
          <label className="block text-sm font-medium text-zinc-400 mb-2">
            {side === "sell" ? "可用数量" : "买入数量"}
          </label>
          <div className="relative">
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="输入数量"
              className="w-full px-4 py-3 pr-16 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-zinc-600 placeholder:text-zinc-600 font-mono"
            />
            {symbol && (
              <button
                type="button"
                onClick={() => setQuantity(String(getPositionQuantity(symbol)))}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-zinc-500 hover:text-zinc-300"
                title="使用全部持仓"
              >
                全部
              </button>
            )}
          </div>
          {side === "sell" && symbol && (
            <p className="text-sm text-zinc-500 mt-1">
              当前持仓: {getPositionQuantity(symbol)} 股
            </p>
          )}
        </div>

        {/* Estimated Amount */}
        {price && quantity && orderType === "limit" && (
          <div className="p-3 bg-zinc-900/50 rounded-lg">
            <p className="text-sm text-zinc-500">
              预计金额: ¥{(parseFloat(price) * parseInt(quantity)).toFixed(2)}
            </p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !symbol || !quantity}
          className={`w-full py-3 rounded-lg font-medium transition-colors ${
            loading
              ? "bg-zinc-800 text-zinc-500"
              : side === "buy"
              ? "bg-red-600 hover:bg-red-500 text-white"
              : "bg-green-600 hover:bg-green-500 text-white"
          }`}
        >
          {loading ? <Spinner size="sm" /> : side === "buy" ? "买入" : "卖出"}
        </button>
      </form>

      {/* Quick Sell Button for Sell Side */}
      {side === "sell" && symbol && getPositionQuantity(symbol) > 0 && (
        <button
          onClick={handleQuickSell}
          disabled={loading}
          className="w-full py-3 border border-zinc-700 rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
        >
          市价快速卖出全部 ({getPositionQuantity(symbol)} 股)
        </button>
      )}
    </div>
  );
}
