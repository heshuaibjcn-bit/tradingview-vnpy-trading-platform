"use client";

import { useState, useEffect } from "react";
import { Play, BarChart3, TrendingUp, TrendingDown, Activity } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface Strategy {
  name: string;
  params: Array<{ key: string; label: string; type: string; default: number }>;
}

interface BacktestResult {
  strategy: string;
  symbol: string;
  period: { start: string; end: string };
  capital: { initial: number; final: number; profit: number };
  metrics: {
    returns: { total: string; annualized: string };
    risk: { max_drawdown: string; sharpe_ratio: string };
    trades: { total: number; winning: number; losing: number; win_rate: string };
    profits: { avg_profit: string; profit_factor: string; expectancy: string };
  };
  equity_curve: Array<{ date: string; equity: number }>;
  trades: Array<{
    entry_time: string;
    exit_time: string;
    symbol: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
  }>;
}

interface BacktestClientProps {
  userId: string;
}

export function BacktestClient({ userId }: BacktestClientProps) {
  const [strategies, setStrategies] = useState<Record<string, Strategy>>({});
  const [selectedStrategy, setSelectedStrategy] = useState("ma_cross");
  const [symbol, setSymbol] = useState("600519");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [parameters, setParameters] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  // Fetch available strategies
  useEffect(() => {
    fetch("/api/backtest")
      .then((res) => res.json())
      .then((data) => {
        setStrategies(data.strategies);
        // Set default parameters for the selected strategy
        if (data.strategies[selectedStrategy]) {
          const defaults: Record<string, number> = {};
          data.strategies[selectedStrategy].params.forEach((p: { key: string; label: string; type: string; default: number }) => {
            defaults[p.key] = p.default;
          });
          setParameters(defaults);
        }
      });
  }, [selectedStrategy]);

  // Update parameters when strategy changes
  useEffect(() => {
    if (strategies[selectedStrategy]) {
      const defaults: Record<string, number> = {};
      strategies[selectedStrategy].params.forEach((p) => {
        defaults[p.key] = p.default;
      });
      setParameters(defaults);
    }
  }, [selectedStrategy, strategies]);

  const runBacktest = async () => {
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId,
          strategy: selectedStrategy,
          symbol,
          startDate,
          endDate,
          parameters,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data.result);
      } else {
        const error = await res.json();
        alert(`回测失败: ${error.error || "未知错误"}`);
      }
    } catch (error) {
      console.error("Backtest error:", error);
      alert("回测失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const currentStrategy = strategies[selectedStrategy];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">策略回测</h1>
          <p className="text-sm text-zinc-500 mt-1">测试交易策略在历史数据上的表现</p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
        <h2 className="text-lg font-semibold text-zinc-100 mb-4">回测配置</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Strategy Selection */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              策略
            </label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              {Object.entries(strategies).map(([key, strategy]) => (
                <option key={key} value={key}>
                  {strategy.name}
                </option>
              ))}
            </select>
          </div>

          {/* Symbol */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              股票代码
            </label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="600519"
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
            />
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              开始日期
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              结束日期
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
            />
          </div>
        </div>

        {/* Strategy Parameters */}
        {currentStrategy && currentStrategy.params.length > 0 && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {currentStrategy.params.map((param) => (
              <div key={param.key}>
                <label className="block text-sm font-medium text-zinc-400 mb-2">
                  {param.label}
                </label>
                <input
                  type="number"
                  value={parameters[param.key] || param.default}
                  onChange={(e) =>
                    setParameters({ ...parameters, [param.key]: parseFloat(e.target.value) })
                  }
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              </div>
            ))}
          </div>
        )}

        {/* Run Button */}
        <div className="mt-6">
          <button
            onClick={runBacktest}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {loading ? <Spinner size="sm" /> : <><Play className="h-4 w-4" /> 运行回测</>}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="总收益率"
              value={result.metrics.returns.total}
              icon={<TrendingUp className="h-5 w-5" />}
              positive={parseFloat(result.metrics.returns.total) >= 0}
            />
            <MetricCard
              label="夏普比率"
              value={result.metrics.risk.sharpe_ratio}
              icon={<BarChart3 className="h-5 w-5" />}
              positive={parseFloat(result.metrics.risk.sharpe_ratio) >= 1}
            />
            <MetricCard
              label="胜率"
              value={result.metrics.trades.win_rate}
              icon={<Activity className="h-5 w-5" />}
              positive={parseFloat(result.metrics.trades.win_rate) >= 50}
            />
            <MetricCard
              label="最大回撤"
              value={result.metrics.risk.max_drawdown}
              icon={<TrendingDown className="h-5 w-5" />}
              positive={false}
            />
          </div>

          {/* Capital Summary */}
          <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
            <h3 className="text-lg font-semibold text-zinc-100 mb-4">资金概览</h3>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-zinc-500">初始资金</p>
                <p className="text-2xl font-mono text-zinc-200">
                  ¥{result.capital.initial.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">最终资金</p>
                <p className="text-2xl font-mono text-zinc-200">
                  ¥{result.capital.final.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">总盈亏</p>
                <p className={`text-2xl font-mono ${
                  result.capital.profit >= 0 ? "text-green-400" : "text-red-400"
                }`}>
                  {result.capital.profit >= 0 ? "+" : ""}¥{result.capital.profit.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Trade History */}
          <div className="border border-zinc-800 rounded-lg bg-zinc-900/50">
            <h3 className="text-lg font-semibold text-zinc-100 p-4 pb-2">交易记录</h3>
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="bg-zinc-800 text-zinc-400 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left">入场</th>
                    <th className="px-4 py-3 text-left">离场</th>
                    <th className="px-4 py-3 text-left">代码</th>
                    <th className="px-4 py-3 text-right">入场价</th>
                    <th className="px-4 py-3 text-right">离场价</th>
                    <th className="px-4 py-3 text-right">数量</th>
                    <th className="px-4 py-3 text-right">盈亏</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((trade, index) => (
                    <tr key={index} className="border-t border-zinc-800">
                      <td className="px-4 py-3 text-zinc-500">
                        {new Date(trade.entry_time).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-zinc-500">
                        {new Date(trade.exit_time).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 font-mono text-zinc-200">{trade.symbol}</td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        ¥{trade.entry_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        ¥{trade.exit_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-zinc-200">
                        {trade.quantity}
                      </td>
                      <td className={`px-4 py-3 text-right font-mono ${
                        trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                      }`}>
                        {trade.pnl >= 0 ? "+" : ""}¥{trade.pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  positive?: boolean;
}

function MetricCard({ label, value, icon, positive = true }: MetricCardProps) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-2 rounded-lg ${positive ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
          {icon}
        </div>
        <span className="text-sm text-zinc-500">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${
        positive ? "text-green-400" : "text-red-400"
      }`}>
        {value}
      </p>
    </div>
  );
}
