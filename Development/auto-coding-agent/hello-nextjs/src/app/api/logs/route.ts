import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Mock trade logs storage
const mockTradeLogs: Array<{
  id: string;
  user_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  order_id: string | null;
  strategy_id: string | null;
  timestamp: string;
  metadata: Record<string, unknown>;
}> = [];

// Mock signal logs storage
const mockSignalLogs: Array<{
  id: string;
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  signal_type: "buy" | "sell" | "hold";
  price: number;
  confidence: number;
  executed: boolean;
  created_at: string;
}> = [];

// Generate mock data
function generateMockTradeLogs(
  userId: string,
  count: number = 50,
): Array<{
  id: string;
  user_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  order_id: string | null;
  strategy_id: string | null;
  timestamp: string;
  metadata: Record<string, unknown>;
}> {
  const symbols = ["000001", "000002", "600000", "600036", "600519"];
  const strategies = ["ma", "macd", "kdj"];
  const logs: Array<{
    id: string;
    user_id: string;
    symbol: string;
    side: "buy" | "sell";
    quantity: number;
    price: number;
    amount: number;
    commission: number;
    order_id: string | null;
    strategy_id: string | null;
    timestamp: string;
    metadata: Record<string, unknown>;
  }> = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const side: "buy" | "sell" = Math.random() > 0.5 ? "buy" : "sell";
    const price = 10 + Math.random() * 50;
    const quantity = 100 + Math.floor(Math.random() * 900);
    const daysAgo = Math.floor(i / 5);

    logs.push({
      id: `trade_${i}`,
      user_id: userId,
      symbol,
      side,
      quantity,
      price: Math.round(price * 100) / 100,
      amount: Math.round(price * quantity * 100) / 100,
      commission: Math.round(price * quantity * 0.0003 * 100) / 100,
      order_id: `order_${i}`,
      strategy_id: strategies[Math.floor(Math.random() * strategies.length)],
      timestamp: new Date(now - daysAgo * 86400000 - Math.random() * 3600000).toISOString(),
      metadata: {},
    });
  }

  return logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

function generateMockSignalLogs(userId: string, count: number = 30) {
  const symbols = ["000001", "000002", "600000", "600036", "600519"];
  const strategies = [
    { id: "ma", name: "均线策略" },
    { id: "macd", name: "MACD策略" },
    { id: "kdj", name: "KDJ策略" },
  ];
  const logs = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const strategy = strategies[Math.floor(Math.random() * strategies.length)];
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const signalTypes: Array<"buy" | "sell" | "hold"> = ["buy", "sell", "hold"];
    const signalType = signalTypes[Math.floor(Math.random() * signalTypes.length)];
    const price = 10 + Math.random() * 50;
    const daysAgo = Math.floor(i / 3);

    logs.push({
      id: `signal_${i}`,
      strategy_id: strategy.id,
      strategy_name: strategy.name,
      symbol,
      signal_type: signalType,
      price: Math.round(price * 100) / 100,
      confidence: Math.round(0.5 + Math.random() * 0.5),
      executed: Math.random() > 0.3,
      created_at: new Date(now - daysAgo * 86400000 - Math.random() * 3600000).toISOString(),
    });
  }

  return logs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

export async function GET(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const type = searchParams.get("type") || "trades";
    const symbol = searchParams.get("symbol");
    const startDate = searchParams.get("start_date");
    const endDate = searchParams.get("end_date");
    const action = searchParams.get("action");

    // Generate mock data for user
    let trades = mockTradeLogs.filter((t) => t.user_id === user.id);
    if (trades.length === 0) {
      trades = generateMockTradeLogs(user.id);
      mockTradeLogs.push(...trades);
    }

    let signals = mockSignalLogs.filter((s) => s.strategy_id.startsWith("s_") || true);
    if (signals.length === 0) {
      signals = generateMockSignalLogs(user.id);
      mockSignalLogs.push(...signals);
    }

    // Statistics action
    if (action === "statistics") {
      const stats = {
        summary: {
          total_trades: trades.length,
          buy_trades: trades.filter((t) => t.side === "buy").length,
          sell_trades: trades.filter((t) => t.side === "sell").length,
          total_buy_amount: trades
            .filter((t) => t.side === "buy")
            .reduce((sum, t) => sum + t.amount, 0),
          total_sell_amount: trades
            .filter((t) => t.side === "sell")
            .reduce((sum, t) => sum + t.amount, 0),
          total_commission: trades.reduce((sum, t) => sum + t.commission, 0),
        },
        symbol_stats: {} as Record<string, unknown>,
        signal_stats: {
          total_signals: signals.length,
          executed_signals: signals.filter((s) => s.executed).length,
          execution_rate: signals.length > 0
            ? (signals.filter((s) => s.executed).length / signals.length) * 100
            : 0,
        },
      };

      // Calculate per-symbol stats
      const symbols = [...new Set(trades.map((t) => t.symbol))];
      for (const sym of symbols) {
        const symTrades = trades.filter((t) => t.symbol === sym);
        const buyTrades = symTrades.filter((t) => t.side === "buy");
        const sellTrades = symTrades.filter((t) => t.side === "sell");

        const totalBuy = buyTrades.reduce((sum, t) => sum + t.amount, 0);
        const totalSell = sellTrades.reduce((sum, t) => sum + t.amount, 0);
        const totalQty = buyTrades.reduce((sum, t) => sum + t.quantity, 0) -
                        sellTrades.reduce((sum, t) => sum + t.quantity, 0);

        stats.symbol_stats[sym] = {
          trade_count: symTrades.length,
          total_buy: Math.round(totalBuy),
          total_sell: Math.round(totalSell),
          net_position: totalQty,
          avg_buy_price: buyTrades.length > 0
            ? Math.round((buyTrades.reduce((sum, t) => sum + t.price, 0) / buyTrades.length) * 100) / 100
            : 0,
          avg_sell_price: sellTrades.length > 0
            ? Math.round((sellTrades.reduce((sum, t) => sum + t.price, 0) / sellTrades.length) * 100) / 100
            : 0,
        };
      }

      return NextResponse.json({ status: "ok", data: stats });
    }

    // Equity curve action
    if (action === "equity_curve") {
      const initialCapital = 100000;
      const equity = initialCapital;
      const curve = [{ timestamp: new Date(Date.now() - 30 * 86400000).toISOString(), equity }];

      // Sort trades by time
      const sortedTrades = [...trades].sort((a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

      let currentEquity = equity;
      for (const trade of sortedTrades) {
        if (trade.side === "sell") {
          currentEquity += trade.amount - trade.commission;
        } else {
          currentEquity -= trade.amount + trade.commission;
        }
        curve.push({
          timestamp: trade.timestamp,
          equity: Math.round(currentEquity * 100) / 100,
        });
      }

      // Calculate performance metrics
      const finalEquity = curve[curve.length - 1].equity;
      const totalReturn = finalEquity - initialCapital;
      const totalReturnPct = (totalReturn / initialCapital) * 100;

      // Calculate max drawdown
      let maxDrawdown = 0;
      let peak = curve[0].equity;
      for (const point of curve) {
        if (point.equity > peak) peak = point.equity;
        const dd = peak - point.equity;
        if (dd > maxDrawdown) maxDrawdown = dd;
      }

      return NextResponse.json({
        status: "ok",
        data: {
          curve,
          initial_capital: initialCapital,
          final_equity: finalEquity,
          total_return: totalReturn,
          total_return_pct: totalReturnPct,
          max_drawdown: maxDrawdown,
          max_drawdown_pct: (maxDrawdown / initialCapital) * 100,
        },
      });
    }

    // Filter by symbol
    if (symbol) {
      trades = trades.filter((t) => t.symbol === symbol);
      signals = signals.filter((s) => s.symbol === symbol);
    }

    // Filter by date range
    if (startDate) {
      const start = new Date(startDate);
      trades = trades.filter((t) => new Date(t.timestamp) >= start);
      signals = signals.filter((s) => new Date(s.created_at) >= start);
    }

    if (endDate) {
      const end = new Date(endDate);
      trades = trades.filter((t) => new Date(t.timestamp) <= end);
      signals = signals.filter((s) => new Date(s.created_at) <= end);
    }

    if (type === "signals") {
      return NextResponse.json({
        status: "ok",
        data: signals,
        total: signals.length,
      });
    }

    return NextResponse.json({
      status: "ok",
      data: trades,
      total: trades.length,
    });
  } catch (error) {
    console.error("Logs API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch logs" },
      { status: 500 }
    );
  }
}
