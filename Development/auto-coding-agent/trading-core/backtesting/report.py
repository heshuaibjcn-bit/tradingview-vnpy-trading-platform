"""
Backtest Report Generator

Generates detailed reports from backtest results.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from .engine import BacktestResult, Trade
from .metrics import format_metrics


def generate_report(result: BacktestResult) -> Dict[str, Any]:
    """Generate a comprehensive backtest report."""
    return {
        "strategy": result.strategy_name,
        "symbol": result.symbol,
        "period": {
            "start": result.start_date,
            "end": result.end_date,
        },
        "capital": {
            "initial": f"¥{result.initial_capital:,.2f}",
            "final": f"¥{result.final_capital:,.2f}",
            "profit": f"¥{result.final_capital - result.initial_capital:,.2f}",
        },
        "metrics": format_metrics(result.metrics),
        "trades": _format_trades(result.trades),
        "parameters": result.parameters,
    }


def generate_html_report(result: BacktestResult) -> str:
    """Generate an HTML report for the backtest."""
    report = generate_report(result)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backtest Report - {result.symbol}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
            .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #007bff; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .summary {{ display: flex; gap: 30px; margin: 20px 0; }}
            .summary-item {{ flex: 1; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Backtest Report</h1>

            <div class="summary">
                <div class="summary-item">
                    <h3>Strategy</h3>
                    <p>{result.strategy_name}</p>
                </div>
                <div class="summary-item">
                    <h3>Symbol</h3>
                    <p>{result.symbol}</p>
                </div>
                <div class="summary-item">
                    <h3>Period</h3>
                    <p>{result.start_date} to {result.end_date}</p>
                </div>
            </div>

            <div class="summary">
                <div class="summary-item">
                    <h3>Initial Capital</h3>
                    <p>¥{result.initial_capital:,.2f}</p>
                </div>
                <div class="summary-item">
                    <h3>Final Capital</h3>
                    <p>¥{result.final_capital:,.2f}</p>
                </div>
                <div class="summary-item">
                    <h3>Total Return</h3>
                    <p class="{"positive" if result.metrics.total_return >= 0 else "negative"}">
                        {result.metrics.total_return:.2%}
                    </p>
                </div>
            </div>

            <h2>Performance Metrics</h2>
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{result.metrics.sharpe_ratio:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">{result.metrics.max_drawdown:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{result.metrics.win_rate:.1%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{result.metrics.profit_factor:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{result.metrics.total_trades}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Annual Return</div>
                    <div class="metric-value {"positive" if result.metrics.annual_return >= 0 else "negative"}">
                        {result.metrics.annual_return:.2%}
                    </div>
                </div>
            </div>

            <h2>Trade History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Entry Time</th>
                        <th>Exit Time</th>
                        <th>Symbol</th>
                        <th>Entry Price</th>
                        <th>Exit Price</th>
                        <th>Quantity</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody>
    """

    for trade in result.trades:
        pnl_class = "positive" if trade.pnl >= 0 else "negative"
        html += f"""
                    <tr>
                        <td>{trade.entry_time.strftime("%Y-%m-%d %H:%M") if trade.entry_time else "N/A"}</td>
                        <td>{trade.exit_time.strftime("%Y-%m-%d %H:%M") if trade.exit_time else "N/A"}</td>
                        <td>{trade.symbol}</td>
                        <td>¥{trade.entry_price:.2f}</td>
                        <td>¥{trade.exit_price:.2f if trade.exit_price else 0:.2f}</td>
                        <td>{int(trade.quantity)}</td>
                        <td class="{pnl_class}">¥{trade.pnl:.2f}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>

            <p style="margin-top: 30px; color: #666; font-size: 12px;">
                Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </p>
        </div>
    </body>
    </html>
    """

    return html


def _format_trades(trades: List[Trade]) -> List[Dict[str, Any]]:
    """Format trades for JSON output."""
    formatted = []
    for trade in trades:
        formatted.append({
            "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
            "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "quantity": int(trade.quantity),
            "pnl": round(trade.pnl, 2),
            "commission": round(trade.commission, 2),
        })
    return formatted
