"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  FileText,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Filter,
  Download,
  RefreshCw,
  Signal,
  Activity,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface LogsClientProps {
  userId: string;
}

interface TradeLog {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  timestamp: string;
  strategy_id: string | null;
}

interface SignalLog {
  id: string;
  strategy_name: string;
  symbol: string;
  signal_type: "buy" | "sell" | "hold";
  price: number;
  confidence: number;
  executed: boolean;
  created_at: string;
}

interface Statistics {
  summary: {
    total_trades: number;
    buy_trades: number;
    sell_trades: number;
    total_buy_amount: number;
    total_sell_amount: number;
    total_commission: number;
  };
  symbol_stats: Record<string, {
    trade_count: number;
    total_buy: number;
    total_sell: number;
    net_position: number;
    avg_buy_price: number;
    avg_sell_price: number;
  }>;
  signal_stats: {
    total_signals: number;
    executed_signals: number;
    execution_rate: number;
  };
}

interface EquityCurveData {
  curve: Array<{ timestamp: string; equity: number }>;
  initial_capital: number;
  final_equity: number;
  total_return: number;
  total_return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
}

type TabType = "trades" | "signals" | "analysis" | "equity";

export function LogsClient({ userId }: LogsClientProps) {
  // userId is used for authentication in parent component
  void userId;
  const [activeTab, setActiveTab] = useState<TabType>("trades");
  const [trades, setTrades] = useState<TradeLog[]>([]);
  const [signals, setSignals] = useState<SignalLog[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [equityData, setEquityData] = useState<EquityCurveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterSymbol, setFilterSymbol] = useState("");
  const [filterType, setFilterType] = useState<"all" | "buy" | "sell">("all");

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch trades
      const tradesRes = await fetch("/api/logs?type=trades");
      if (tradesRes.ok) {
        const data = await tradesRes.json();
        setTrades(data.data || []);
      }

      // Fetch signals
      const signalsRes = await fetch("/api/logs?type=signals");
      if (signalsRes.ok) {
        const data = await signalsRes.json();
        setSignals(data.data || []);
      }

      // Fetch statistics
      const statsRes = await fetch("/api/logs?action=statistics");
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStatistics(data.data);
      }

      // Fetch equity curve
      const equityRes = await fetch("/api/logs?action=equity_curve");
      if (equityRes.ok) {
        const data = await equityRes.json();
        setEquityData(data.data);
      }
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Draw equity curve chart
  useEffect(() => {
    if (activeTab === "equity" && equityData && canvasRef.current) {
      drawEquityChart(canvasRef.current, equityData);
    }
  }, [activeTab, equityData]);

  const handleExport = async () => {
    const data = activeTab === "trades" ? trades : signals;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeTab}_export_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredTrades = trades.filter((t) => {
    if (filterSymbol && !t.symbol.includes(filterSymbol)) return false;
    if (filterType !== "all" && t.side !== filterType) return false;
    return true;
  });

  const filteredSignals = signals.filter((s) => {
    if (filterSymbol && !s.symbol.includes(filterSymbol)) return false;
    return true;
  });

  const allSymbols = Array.from(
    new Set([...trades.map((t) => t.symbol), ...signals.map((s) => s.symbol)])
  ).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">交易日志</h1>
          <p className="text-sm text-zinc-500 mt-1">查看交易记录和策略信号</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
            title="刷新"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            导出
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard
            icon={<Activity className="h-5 w-5 text-blue-400" />}
            label="总交易次数"
            value={statistics.summary.total_trades.toString()}
          />
          <SummaryCard
            icon={<TrendingUp className="h-5 w-5 text-green-400" />}
            label="买入金额"
            value={`¥${(statistics.summary.total_buy_amount / 10000).toFixed(1)}万`}
          />
          <SummaryCard
            icon={<TrendingDown className="h-5 w-5 text-red-400" />}
            label="卖出金额"
            value={`¥${(statistics.summary.total_sell_amount / 10000).toFixed(1)}万`}
          />
          <SummaryCard
            icon={<Signal className="h-5 w-5 text-yellow-400" />}
            label="信号执行率"
            value={`${statistics.signal_stats.execution_rate.toFixed(0)}%`}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        <TabButton active={activeTab === "trades"} onClick={() => setActiveTab("trades")}>
          <FileText className="h-4 w-4 mr-2" />
          交易记录
          <span className="ml-2 text-zinc-500">({trades.length})</span>
        </TabButton>
        <TabButton active={activeTab === "signals"} onClick={() => setActiveTab("signals")}>
          <Signal className="h-4 w-4 mr-2" />
          策略信号
          <span className="ml-2 text-zinc-500">({signals.length})</span>
        </TabButton>
        <TabButton active={activeTab === "analysis"} onClick={() => setActiveTab("analysis")}>
          <BarChart3 className="h-4 w-4 mr-2" />
          统计分析
        </TabButton>
        <TabButton active={activeTab === "equity"} onClick={() => setActiveTab("equity")}>
          <TrendingUp className="h-4 w-4 mr-2" />
            收益曲线
        </TabButton>
      </div>

      {/* Filters */}
      {(activeTab === "trades" || activeTab === "signals") && (
        <div className="flex items-center gap-4 py-2">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-zinc-500" />
            <select
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option value="">全部股票</option>
              {allSymbols.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          {activeTab === "trades" && (
            <div className="flex items-center gap-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as "all" | "buy" | "sell")}
                className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-200 focus:outline-none focus:border-zinc-600"
              >
                <option value="all">全部类型</option>
                <option value="buy">买入</option>
                <option value="sell">卖出</option>
              </select>
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : (
        <>
          {/* Trades Table */}
          {activeTab === "trades" && (
            <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900">
                    <TableHead>时间</TableHead>
                    <TableHead>股票</TableHead>
                    <TableHead>方向</TableHead>
                    <TableHead>数量</TableHead>
                    <TableHead>价格</TableHead>
                    <TableHead>金额</TableHead>
                    <TableHead>手续费</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {filteredTrades.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-zinc-500">
                        暂无交易记录
                      </td>
                    </tr>
                  ) : (
                    filteredTrades.map((trade) => (
                      <tr key={trade.id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                        <td className="px-4 py-3 text-sm text-zinc-400">
                          {new Date(trade.timestamp).toLocaleString("zh-CN")}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-zinc-200">
                          {trade.symbol}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.side === "buy"
                              ? "bg-red-500/20 text-red-400"
                              : "bg-green-500/20 text-green-400"
                          }`}>
                            {trade.side === "buy" ? "买入" : "卖出"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-300">{trade.quantity}</td>
                        <td className="px-4 py-3 text-sm text-zinc-300">
                          ¥{trade.price.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-300">
                          ¥{trade.amount.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-500">
                          ¥{trade.commission.toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Signals Table */}
          {activeTab === "signals" && (
            <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900">
                    <TableHead>时间</TableHead>
                    <TableHead>策略</TableHead>
                    <TableHead>股票</TableHead>
                    <TableHead>信号类型</TableHead>
                    <TableHead>价格</TableHead>
                    <TableHead>置信度</TableHead>
                    <TableHead>状态</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {filteredSignals.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-zinc-500">
                        暂无信号记录
                      </td>
                    </tr>
                  ) : (
                    filteredSignals.map((signal) => (
                      <tr key={signal.id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                        <td className="px-4 py-3 text-sm text-zinc-400">
                          {new Date(signal.created_at).toLocaleString("zh-CN")}
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-300">
                          {signal.strategy_name}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-zinc-200">
                          {signal.symbol}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            signal.signal_type === "buy"
                              ? "bg-red-500/20 text-red-400"
                              : signal.signal_type === "sell"
                              ? "bg-green-500/20 text-green-400"
                              : "bg-zinc-500/20 text-zinc-400"
                          }`}>
                            {signal.signal_type === "buy" ? "买入" : signal.signal_type === "sell" ? "卖出" : "持有"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-300">
                          ¥{signal.price.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm text-zinc-300">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-zinc-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500"
                                style={{ width: `${signal.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs">{(signal.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            signal.executed
                              ? "bg-green-500/20 text-green-400"
                              : "bg-zinc-500/20 text-zinc-400"
                          }`}>
                            {signal.executed ? "已执行" : "未执行"}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Analysis Tab */}
          {activeTab === "analysis" && statistics && (
            <div className="space-y-6">
              {/* Trading Summary */}
              <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                <h3 className="text-lg font-semibold text-zinc-100 mb-4">交易汇总</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                  <MetricItem label="买入次数" value={statistics.summary.buy_trades.toString()} />
                  <MetricItem label="卖出次数" value={statistics.summary.sell_trades.toString()} />
                  <MetricItem label="总买入金额" value={`¥${statistics.summary.total_buy_amount.toLocaleString()}`} />
                  <MetricItem label="总卖出金额" value={`¥${statistics.summary.total_sell_amount.toLocaleString()}`} />
                  <MetricItem label="总手续费" value={`¥${statistics.summary.total_commission.toFixed(2)}`} />
                  <MetricItem
                    label="净交易额"
                    value={`¥${(statistics.summary.total_sell_amount - statistics.summary.total_buy_amount - statistics.summary.total_commission).toLocaleString()}`}
                    valueClass={(statistics.summary.total_sell_amount - statistics.summary.total_buy_amount - statistics.summary.total_commission) >= 0 ? "text-green-400" : "text-red-400"}
                  />
                </div>
              </div>

              {/* Per-Symbol Stats */}
              {Object.keys(statistics.symbol_stats).length > 0 && (
                <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                  <h3 className="text-lg font-semibold text-zinc-100 mb-4">个股统计</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-zinc-800">
                          <TableHead>股票</TableHead>
                          <TableHead>交易次数</TableHead>
                          <TableHead>买入总额</TableHead>
                          <TableHead>卖出总额</TableHead>
                          <TableHead>持仓</TableHead>
                          <TableHead>均价</TableHead>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(statistics.symbol_stats).map(([symbol, stats]) => (
                          <tr key={symbol} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                            <td className="px-4 py-3 text-sm font-medium text-zinc-200">
                              {symbol}
                            </td>
                            <td className="px-4 py-3 text-sm text-zinc-300">
                              {stats.trade_count}
                            </td>
                            <td className="px-4 py-3 text-sm text-red-400">
                              ¥{stats.total_buy.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-sm text-green-400">
                              ¥{stats.total_sell.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-sm text-zinc-300">
                              {stats.net_position}
                            </td>
                            <td className="px-4 py-3 text-sm text-zinc-300">
                              ¥{stats.avg_buy_price.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Equity Curve Tab */}
          {activeTab === "equity" && equityData && (
            <div className="space-y-6">
              {/* Summary Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                  label="初始资金"
                  value={`¥${equityData.initial_capital.toLocaleString()}`}
                />
                <MetricCard
                  label="当前资金"
                  value={`¥${equityData.final_equity.toLocaleString()}`}
                  valueClass={equityData.total_return >= 0 ? "text-green-400" : "text-red-400"}
                />
                <MetricCard
                  label="总收益"
                  value={`${equityData.total_return_pct.toFixed(2)}%`}
                  valueClass={equityData.total_return >= 0 ? "text-green-400" : "text-red-400"}
                />
                <MetricCard
                  label="最大回撤"
                  value={`-${equityData.max_drawdown_pct.toFixed(2)}%`}
                  valueClass="text-red-400"
                />
              </div>

              {/* Chart */}
              <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-900/50">
                <h3 className="text-lg font-semibold text-zinc-100 mb-4">收益曲线</h3>
                <div className="relative h-64">
                  <canvas ref={canvasRef} className="w-full h-full" />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Helper components
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 font-medium transition-colors flex items-center ${
        active
          ? "text-blue-400 border-b-2 border-blue-400"
          : "text-zinc-500 hover:text-zinc-300"
      }`}
    >
      {children}
    </button>
  );
}

function TableHead({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">{children}</th>;
}

function SummaryCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-zinc-500">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-zinc-100">{value}</p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  valueClass = "text-zinc-200",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
      <p className="text-sm text-zinc-500 mb-1">{label}</p>
      <p className={`text-xl font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}

function MetricItem({
  label,
  value,
  valueClass = "text-zinc-200",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div>
      <p className="text-sm text-zinc-500">{label}</p>
      <p className={`text-lg font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}

// Chart drawing function
function drawEquityChart(canvas: HTMLCanvasElement, data: EquityCurveData) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Set canvas size
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * 2; // HiDPI
  canvas.height = rect.height * 2;
  ctx.scale(2, 2);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 20, right: 20, bottom: 30, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  // Find min/max values
  const values = data.curve.map((p) => p.equity);
  const minValue = Math.min(...values, data.initial_capital);
  const maxValue = Math.max(...values, data.initial_capital);
  const range = maxValue - minValue || 1;

  // Draw grid lines
  ctx.strokeStyle = "#27272a";
  ctx.lineWidth = 1;

  // Horizontal grid
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartHeight / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    // Y-axis labels
    const value = maxValue - (range / 5) * i;
    ctx.fillStyle = "#71717a";
    ctx.font = "11px system-ui";
    ctx.textAlign = "right";
    ctx.fillText(`¥${value.toFixed(0)}`, padding.left - 10, y + 4);
  }

  // Draw equity line
  if (data.curve.length > 1) {
    ctx.beginPath();
    ctx.strokeStyle = data.total_return >= 0 ? "#22c55e" : "#ef4444";
    ctx.lineWidth = 2;

    data.curve.forEach((point, i) => {
      const x = padding.left + (chartWidth / (data.curve.length - 1)) * i;
      const y = padding.top + chartHeight - ((point.equity - minValue) / range) * chartHeight;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Fill area under line
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.closePath();
    ctx.fillStyle = data.total_return >= 0 ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)";
    ctx.fill();
  }

  // Draw initial capital line
  const initialY = padding.top + chartHeight - ((data.initial_capital - minValue) / range) * chartHeight;
  ctx.beginPath();
  ctx.strokeStyle = "#71717a";
  ctx.lineWidth = 1;
  ctx.setLineDash([5, 5]);
  ctx.moveTo(padding.left, initialY);
  ctx.lineTo(width - padding.right, initialY);
  ctx.stroke();
  ctx.setLineDash([]);

  // X-axis labels (first and last date)
  ctx.fillStyle = "#71717a";
  ctx.textAlign = "left";
  if (data.curve.length > 0) {
    const firstDate = new Date(data.curve[0].timestamp);
    const lastDate = new Date(data.curve[data.curve.length - 1].timestamp);
    ctx.fillText(firstDate.toLocaleDateString("zh-CN"), padding.left, height - 10);
    ctx.textAlign = "right";
    ctx.fillText(lastDate.toLocaleDateString("zh-CN"), width - padding.right, height - 10);
  }
}
