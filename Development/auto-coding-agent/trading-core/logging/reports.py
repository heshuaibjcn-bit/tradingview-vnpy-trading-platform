"""
Report generation module for trading analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import json
from loguru import logger

from .models import TradeLog, SignalLog
from .analyzer import TradeAnalyzer, TradingStatistics, PerformanceMetrics


@dataclass
class ReportPeriod:
    """Report period configuration."""
    start_date: datetime
    end_date: datetime
    name: str

    @classmethod
    def today(cls) -> "ReportPeriod":
        """Create a report for today."""
        now = datetime.now()
        return cls(
            start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            name="今日",
        )

    @classmethod
    def this_week(cls) -> "ReportPeriod":
        """Create a report for this week."""
        now = datetime.now()
        start = now - timedelta(days=now.weekday())
        return cls(
            start_date=start.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            name="本周",
        )

    @classmethod
    def this_month(cls) -> "ReportPeriod":
        """Create a report for this month."""
        now = datetime.now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return cls(
            start_date=start,
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            name="本月",
        )

    @classmethod
    def custom(cls, start: datetime, end: datetime, name: str = "自定义") -> "ReportPeriod":
        """Create a custom report period."""
        return cls(
            start_date=start,
            end_date=end,
            name=name,
        )


@dataclass
class TradingReport:
    """Complete trading report."""
    period: ReportPeriod
    generated_at: datetime = field(default_factory=datetime.now)
    statistics: Optional[TradingStatistics] = None
    performance: Optional[PerformanceMetrics] = None
    signal_analysis: Optional[Dict] = None
    trades: List[TradeLog] = field(default_factory=list)
    top_winners: List[Dict] = field(default_factory=list)
    top_losers: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "period": {
                "name": self.period.name,
                "start_date": self.period.start_date.isoformat(),
                "end_date": self.period.end_date.isoformat(),
            },
            "generated_at": self.generated_at.isoformat(),
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "performance": self.performance.to_dict() if self.performance else None,
            "signal_analysis": self.signal_analysis,
            "trades_count": len(self.trades),
            "top_winners": self.top_winners,
            "top_losers": self.top_losers,
        }


class ReportGenerator:
    """Generates trading reports."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.analyzer = TradeAnalyzer()

    def generate_report(
        self,
        trades: List[TradeLog],
        signals: List[SignalLog],
        period: ReportPeriod,
        initial_capital: float = 100000.0,
    ) -> TradingReport:
        """Generate a complete trading report."""
        # Filter trades by period
        period_trades = [
            t for t in trades
            if period.start_date <= t.timestamp <= period.end_date
        ]
        period_signals = [
            s for s in signals
            if period.start_date <= s.created_at <= period.end_date
        ]

        # Create analyzer with filtered data
        self.analyzer = TradeAnalyzer()
        self.analyzer.add_trades(period_trades)
        self.analyzer.add_signals(period_signals)

        # Generate report
        report = TradingReport(period=period)
        report.trades = period_trades

        # Calculate statistics
        report.statistics = self.analyzer.calculate_statistics()

        # Calculate performance
        report.performance = self.analyzer.calculate_performance(initial_capital)

        # Analyze signals
        report.signal_analysis = self.analyzer.calculate_signal_analysis()

        # Top winners and losers
        positions = self.analyzer._group_positions(period_trades)
        sorted_positions = sorted(positions, key=lambda p: p["pnl"], reverse=True)

        report.top_winners = [
            {"symbol": p["symbol"], "pnl": p["pnl"], "return_pct": (p["pnl"] / (p["entry_price"] * p["quantity"]) * 100) if p["quantity"] > 0 else 0}
            for p in sorted_positions[:5] if p["pnl"] > 0
        ]
        report.top_losers = [
            {"symbol": p["symbol"], "pnl": p["pnl"], "return_pct": (p["pnl"] / (p["entry_price"] * p["quantity"]) * 100) if p["quantity"] > 0 else 0}
            for p in sorted_positions[-5:][::-1] if p["pnl"] < 0
        ]

        logger.info(f"Generated {period.name} report with {len(period_trades)} trades")
        return report

    def save_report(self, report: TradingReport, filename: Optional[str] = None) -> str:
        """Save report to JSON file."""
        if filename is None:
            date_str = report.period.start_date.strftime("%Y%m%d")
            filename = f"report_{report.period.name}_{date_str}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Report saved to {filepath}")
        return str(filepath)

    def generate_html_report(self, report: TradingReport) -> str:
        """Generate an HTML report."""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.period.name}交易报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #09090b;
            color: #e4e4e7;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            border-bottom: 1px solid #27272a;
            padding-bottom: 10px;
        }}
        .period {{
            color: #71717a;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .metric {{
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            padding: 16px;
        }}
        .metric-label {{
            color: #71717a;
            font-size: 12px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 600;
        }}
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #27272a;
        }}
        th {{
            background: #18181b;
            font-weight: 500;
        }}
        tr:hover {{
            background: #18181b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report.period.name}交易报告</h1>
        <p class="period">
            {report.period.start_date.strftime("%Y-%m-%d %H:%M")} 至
            {report.period.end_date.strftime("%Y-%m-%d %H:%M")}
        </p>
"""

        # Summary metrics
        if report.performance:
            perf = report.performance
            return_class = "positive" if perf.total_return >= 0 else "negative"
            html += f"""
        <div class="summary">
            <div class="metric">
                <div class="metric-label">总收益</div>
                <div class="metric-value {return_class}">¥{perf.total_return:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">收益率</div>
                <div class="metric-value {return_class}">{perf.total_return_pct:.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">交易次数</div>
                <div class="metric-value">{report.statistics.total_trades if report.statistics else 0}</div>
            </div>
            <div class="metric">
                <div class="metric-label">胜率</div>
                <div class="metric-value">{perf.win_rate:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value negative">{perf.max_drawdown_pct:.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{perf.sharpe_ratio:.2f}</div>
            </div>
        </div>
"""

        # Top winners
        if report.top_winners:
            html += """
        <div class="section">
            <h2>📈 最佳交易</h2>
            <table>
                <thead>
                    <tr>
                        <th>股票</th>
                        <th>收益</th>
                        <th>收益率</th>
                    </tr>
                </thead>
                <tbody>
"""
            for winner in report.top_winners:
                html += f"""
                    <tr>
                        <td>{winner['symbol']}</td>
                        <td class="positive">¥{winner['pnl']:,.2f}</td>
                        <td class="positive">{winner['return_pct']:.2f}%</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""

        # Top losers
        if report.top_losers:
            html += """
        <div class="section">
            <h2>📉 最差交易</h2>
            <table>
                <thead>
                    <tr>
                        <th>股票</th>
                        <th>亏损</th>
                        <th>亏损率</th>
                    </tr>
                </thead>
                <tbody>
"""
            for loser in report.top_losers:
                html += f"""
                    <tr>
                        <td>{loser['symbol']}</td>
                        <td class="negative">¥{loser['pnl']:,.2f}</td>
                        <td class="negative">{loser['return_pct']:.2f}%</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""

        # Signal analysis
        if report.signal_analysis:
            sa = report.signal_analysis
            html += f"""
        <div class="section">
            <h2>📊 信号分析</h2>
            <div class="summary">
                <div class="metric">
                    <div class="metric-label">总信号数</div>
                    <div class="metric-value">{sa.get('total_signals', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">执行信号</div>
                    <div class="metric-value">{sa.get('executed_signals', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">执行率</div>
                    <div class="metric-value">{sa.get('execution_rate', 0):.1f}%</div>
                </div>
            </div>
        </div>
"""

        html += """
        <div class="period" style="margin-top: 40px; text-align: center;">
            报告生成时间: """ + report.generated_at.strftime("%Y-%m-%d %H:%M:%S") + """
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_summary_report(self, reports: List[TradingReport]) -> str:
        """Generate a summary comparing multiple periods."""
        if not reports:
            return ""

        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>交易汇总报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #09090b;
            color: #e4e4e7;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            border-bottom: 1px solid #27272a;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #27272a;
        }
        th {
            background: #18181b;
        }
        .positive { color: #22c55e; }
        .negative { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>交易汇总报告</h1>
        <table>
            <thead>
                <tr>
                    <th>周期</th>
                    <th>交易次数</th>
                    <th>总收益</th>
                    <th>收益率</th>
                    <th>胜率</th>
                    <th>夏普比率</th>
                </tr>
            </thead>
            <tbody>
"""

        for report in reports:
            if report.performance and report.statistics:
                perf = report.performance
                stats = report.statistics
                return_class = "positive" if perf.total_return >= 0 else "negative"
                html += f"""
                <tr>
                    <td>{report.period.name}</td>
                    <td>{stats.total_trades}</td>
                    <td class="{return_class}">¥{perf.total_return:,.2f}</td>
                    <td class="{return_class}">{perf.total_return_pct:.2f}%</td>
                    <td>{perf.win_rate:.1f}%</td>
                    <td>{perf.sharpe_ratio:.2f}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
