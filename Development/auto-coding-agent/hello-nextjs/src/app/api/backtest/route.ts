import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Types for backtest request
interface BacktestRequest {
  userId: string;
  strategy: string;
  symbol: string;
  startDate: string;
  endDate: string;
  parameters?: Record<string, string | number>;
}

// Built-in strategy configurations
const STRATEGIES: Record<string, { name: string; params: Array<{ key: string; label: string; type: string; default: number }> }> = {
  ma_cross: {
    name: "均线交叉",
    params: [
      { key: "short_period", label: "短期均线", type: "number", default: 5 },
      { key: "long_period", label: "长期均线", type: "number", default: 20 },
    ],
  },
  rsi: {
    name: "RSI策略",
    params: [
      { key: "period", label: "RSI周期", type: "number", default: 14 },
      { key: "oversold", label: "超卖线", type: "number", default: 30 },
      { key: "overbought", label: "超买线", type: "number", default: 70 },
    ],
  },
};

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body: BacktestRequest = await request.json();
    const { userId, strategy, symbol, startDate, endDate, parameters = {} } = body;

    // Verify user ID matches
    if (userId !== user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Validate inputs
    if (!strategy || !symbol || !startDate || !endDate) {
      return NextResponse.json(
        { error: "Missing required fields: strategy, symbol, startDate, endDate" },
        { status: 400 }
      );
    }

    if (!STRATEGIES[strategy]) {
      return NextResponse.json(
        { error: `Unknown strategy: ${strategy}` },
        { status: 400 }
      );
    }

    // For now, return mock backtest results
    // In production, this would call the Python backend
    const mockResult = generateMockBacktest(strategy, symbol, startDate, endDate, parameters);

    return NextResponse.json({
      status: "ok",
      result: mockResult,
    });
  } catch (error) {
    console.error("Backtest error:", error);
    return NextResponse.json(
      { error: "Failed to run backtest" },
      { status: 500 }
    );
  }
}

export async function GET() {
  // Return available strategies
  return NextResponse.json({
    strategies: STRATEGIES,
  });
}

function generateMockBacktest(
  strategy: string,
  symbol: string,
  startDate: string,
  endDate: string,
  parameters: Record<string, string | number>
) {
  // Generate mock backtest results
  const initialCapital = 100000;
  const days = Math.floor((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24));

  // Random but realistic metrics
  const totalReturn = (Math.random() * 0.6) - 0.1; // -10% to +50%
  const finalCapital = initialCapital * (1 + totalReturn);
  const maxDrawdown = -Math.random() * 0.3; // 0 to -30%

  // Generate equity curve
  const equityCurve = [];
  let equity = initialCapital;
  for (let i = 0; i <= Math.min(days, 252); i++) {
    const dailyReturn = (Math.random() - 0.45) * 0.03; // Slight upward bias
    equity = equity * (1 + dailyReturn);
    equityCurve.push({
      date: new Date(new Date(startDate).getTime() + i * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
      equity: Math.round(equity * 100) / 100,
    });
  }

  // Generate trades
  const tradeCount = Math.floor(Math.random() * 30) + 5;
  const trades = [];
  for (let i = 0; i < tradeCount; i++) {
    const entryTime = new Date(new Date(startDate).getTime() + Math.random() * days * 24 * 60 * 60 * 1000);
    const exitTime = new Date(entryTime.getTime() + Math.random() * 30 * 24 * 60 * 60 * 1000);
    const entryPrice = 10 + Math.random() * 50;
    const exitPrice = entryPrice * (1 + (Math.random() - 0.4) * 0.1);
    const quantity = 100 + Math.floor(Math.random() * 10) * 100;
    const pnl = (exitPrice - entryPrice) * quantity;

    trades.push({
      entry_time: entryTime.toISOString(),
      exit_time: exitTime.toISOString(),
      symbol,
      side: "long",
      entry_price: Math.round(entryPrice * 100) / 100,
      exit_price: Math.round(exitPrice * 100) / 100,
      quantity,
      pnl: Math.round(pnl * 100) / 100,
    });
  }

  // Calculate metrics
  const winningTrades = trades.filter(t => t.pnl > 0).length;
  const losingTrades = trades.filter(t => t.pnl < 0).length;
  const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);

  return {
    strategy: STRATEGIES[strategy].name,
    symbol,
    period: { start: startDate, end: endDate },
    capital: {
      initial: initialCapital,
      final: Math.round(finalCapital),
      profit: Math.round(finalCapital - initialCapital),
    },
    metrics: {
      returns: {
        total: `${(totalReturn * 100).toFixed(2)}%`,
        annualized: `${((Math.pow(1 + totalReturn, 252 / days) - 1) * 100).toFixed(2)}%`,
        daily_mean: "0.02%",
        daily_std: "1.5%",
      },
      risk: {
        max_drawdown: `${(maxDrawdown * 100).toFixed(2)}%`,
        drawdown_duration: "15 days",
        sharpe_ratio: (totalReturn / 0.15).toFixed(2),
        sortino_ratio: (totalReturn / 0.12).toFixed(2),
      },
      trades: {
        total: tradeCount,
        winning: winningTrades,
        losing: losingTrades,
        win_rate: `${((winningTrades / tradeCount) * 100).toFixed(1)}%`,
      },
      profits: {
        avg_profit: `¥${trades.filter(t => t.pnl > 0).reduce((s, t) => s + t.pnl, 0) / Math.max(winningTrades, 1) | 0}`,
        avg_loss: `¥${Math.abs(trades.filter(t => t.pnl < 0).reduce((s, t) => s + t.pnl, 0) / Math.max(losingTrades, 1) | 0)}`,
        profit_factor: winningTrades > 0 ? (trades.filter(t => t.pnl > 0).reduce((s, t) => s + t.pnl, 0) /
          Math.abs(trades.filter(t => t.pnl < 0).reduce((s, t) => s + t.pnl, 0) || 1)).toFixed(2) : "0",
        expectancy: `¥${(totalPnL / tradeCount).toFixed(2)}`,
      },
    },
    equity_curve: equityCurve,
    trades,
    parameters,
  };
}
