"use client";

import { useCallback, useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface MarketWatchProps {
  symbols: string[];
}

interface QuoteData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  volume: number;
}

// Default symbols to watch
const DEFAULT_SYMBOLS = ["000001", "000002", "600000", "600036", "600519"];

export function MarketWatch({ symbols }: MarketWatchProps) {
  const [quotes, setQuotes] = useState<QuoteData[]>([]);
  const [loading, setLoading] = useState(true);

  // Use provided symbols or defaults
  const watchList = symbols.length > 0 ? symbols : DEFAULT_SYMBOLS;

  // Fetch quotes data
  const fetchQuotes = useCallback(async () => {
    try {
      setLoading(true);
      // For demo, use mock data. In production, this would call the real API
      const mockQuotes: QuoteData[] = watchList.map((symbol) => ({
        symbol,
        name: getStockName(symbol),
        price: 10 + Math.random() * 50,
        change: (Math.random() - 0.5) * 5,
        changePercent: (Math.random() - 0.5) * 10,
        high: 10 + Math.random() * 50,
        low: 10 + Math.random() * 50,
        volume: Math.floor(Math.random() * 1000000),
      }));
      setQuotes(mockQuotes);
    } catch (error) {
      console.error("Failed to fetch quotes:", error);
    } finally {
      setLoading(false);
    }
  }, [watchList]);

  useEffect(() => {
    fetchQuotes();
    const interval = setInterval(fetchQuotes, 3000);
    return () => clearInterval(interval);
  }, [fetchQuotes]);

  return (
    <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 p-4 dark:border-zinc-800">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-zinc-500" />
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            行情监控
          </h2>
        </div>
        <span className="text-xs text-zinc-500">每3秒更新</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-zinc-600 dark:text-zinc-400">代码</th>
              <th className="px-4 py-3 text-left font-medium text-zinc-600 dark:text-zinc-400">名称</th>
              <th className="px-4 py-3 text-right font-medium text-zinc-600 dark:text-zinc-400">现价</th>
              <th className="px-4 py-3 text-right font-medium text-zinc-600 dark:text-zinc-400">涨跌</th>
              <th className="px-4 py-3 text-right font-medium text-zinc-600 dark:text-zinc-400">涨跌幅</th>
              <th className="px-4 py-3 text-right font-medium text-zinc-600 dark:text-zinc-400">成交量</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {quotes.map((quote) => {
              const isPositive = quote.change >= 0;
              return (
                <tr key={quote.symbol} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                  <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                    {quote.symbol}
                  </td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                    {quote.name}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-zinc-900 dark:text-zinc-100">
                    ¥{quote.price.toFixed(2)}
                  </td>
                  <td className={`px-4 py-3 text-right font-medium ${
                    isPositive ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"
                  }`}>
                    <div className="flex items-center justify-end gap-1">
                      {isPositive ? (
                        <TrendingUp className="h-3.5 w-3.5" />
                      ) : (
                        <TrendingDown className="h-3.5 w-3.5" />
                      )}
                      {isPositive ? "+" : ""}{quote.change.toFixed(2)}
                    </div>
                  </td>
                  <td className={`px-4 py-3 text-right font-medium ${
                    isPositive ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"
                  }`}>
                    {isPositive ? "+" : ""}{quote.changePercent.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-600 dark:text-zinc-400">
                    {formatVolume(quote.volume)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {loading && quotes.length === 0 && (
        <div className="p-8 text-center text-zinc-500">
          <Activity className="mx-auto h-8 w-8 animate-pulse" />
          <p className="mt-2">加载行情数据...</p>
        </div>
      )}
    </div>
  );
}

// Helper function to get stock name (simplified)
function getStockName(symbol: string): string {
  const names: Record<string, string> = {
    "000001": "平安银行",
    "000002": "万科A",
    "600000": "浦发银行",
    "600036": "招商银行",
    "600519": "贵州茅台",
  };
  return names[symbol] || "未知";
}

// Helper function to format volume
function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`;
  }
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`;
  }
  return volume.toString();
}
