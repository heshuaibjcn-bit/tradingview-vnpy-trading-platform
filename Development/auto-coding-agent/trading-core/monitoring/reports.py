"""
Performance Report Generator

Generates performance reports and summaries.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import json

from .metrics import PerformanceMetrics, MetricsCollector
from .alerts import Alert, AlertSeverity


class PerformanceReport:
    """Performance report data"""

    def __init__(
        self,
        report_id: str,
        start_time: str,
        end_time: str,
        metrics_summary: Dict[str, Any],
        alerts_summary: Dict[str, Any],
        top_issues: List[Dict[str, Any]],
        recommendations: List[str],
    ):
        self.report_id = report_id
        self.start_time = start_time
        self.end_time = end_time
        self.metrics_summary = metrics_summary
        self.alerts_summary = alerts_summary
        self.top_issues = top_issues
        self.recommendations = recommendations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metrics_summary": self.metrics_summary,
            "alerts_summary": self.alerts_summary,
            "top_issues": self.top_issues,
            "recommendations": self.recommendations,
            "generated_at": datetime.now().isoformat(),
        }

    def to_markdown(self) -> str:
        """Convert to Markdown format"""
        lines = [
            f"# Performance Report",
            f"\n**Report ID**: {self.report_id}",
            f"**Period**: {self.start_time} to {self.end_time}",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Metrics Summary",
            "",
        ]

        # Metrics
        if "cpu" in self.metrics_summary:
            cpu = self.metrics_summary["cpu"]
            lines.extend([
                "### CPU Usage",
                f"- Average: {cpu['avg']}%",
                f"- Maximum: {cpu['max']}%",
                f"- Minimum: {cpu['min']}%",
                "",
            ])

        if "memory" in self.metrics_summary:
            mem = self.metrics_summary["memory"]
            lines.extend([
                "### Memory Usage",
                f"- Average: {mem['avg']}%",
                f"- Maximum: {mem['max']}%",
                f"- Minimum: {mem['min']}%",
                "",
            ])

        if "throughput" in self.metrics_summary:
            tp = self.metrics_summary["throughput"]
            lines.extend([
                "### Message Throughput",
                f"- Average: {tp['avg']} msg/s",
                f"- Maximum: {tp['max']} msg/s",
                f"- Current: {tp['current']} msg/s",
                "",
            ])

        # Alerts
        if self.alerts_summary:
            lines.extend([
                "## Alerts Summary",
                "",
                f"- Total Alerts: {self.alerts_summary.get('total_alerts', 0)}",
                f"- Active Alerts: {self.alerts_summary.get('active_alerts', 0)}",
                "",
            ])

            by_severity = self.alerts_summary.get('by_severity', {})
            if by_severity:
                lines.extend([
                    "### By Severity",
                    f"- Info: {by_severity.get('info', 0)}",
                    f"- Warning: {by_severity.get('warning', 0)}",
                    f"- Error: {by_severity.get('error', 0)}",
                    f"- Critical: {by_severity.get('critical', 0)}",
                    "",
                ])

        # Issues
        if self.top_issues:
            lines.extend([
                "## Top Issues",
                "",
            ])
            for i, issue in enumerate(self.top_issues, 1):
                lines.append(f"{i}. **{issue.get('title', 'Unknown')}**")
                lines.append(f"   - {issue.get('description', '')}")
                lines.append(f"   - Severity: {issue.get('severity', 'unknown')}")
                lines.append("")

        # Recommendations
        if self.recommendations:
            lines.extend([
                "## Recommendations",
                "",
            ])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


class ReportGenerator:
    """
    Generates performance reports from metrics and alerts
    """

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        alert_engine=None,
        output_dir: str = "data/reports",
    ):
        """
        Initialize report generator

        Args:
            metrics_collector: MetricsCollector to get data from
            alert_engine: Optional AlertEngine for alert data
            output_dir: Directory to save reports
        """
        self.metrics_collector = metrics_collector
        self.alert_engine = alert_engine
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("ReportGenerator initialized")

    def generate_report(
        self,
        hours: int = 24,
        report_id: Optional[str] = None,
    ) -> PerformanceReport:
        """
        Generate performance report

        Args:
            hours: Number of hours to report on
            report_id: Optional report ID

        Returns:
            PerformanceReport
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        if not report_id:
            report_id = f"report_{start_time.strftime('%Y%m%d_%H%M%S')}"

        # Get metrics summary
        metrics_summary = self.metrics_collector.get_metrics_summary()

        # Get alerts summary
        alerts_summary = {}
        if self.alert_engine:
            alerts_summary = self.alert_engine.get_alert_summary()

        # Identify top issues
        top_issues = self._identify_issues(metrics_summary, alerts_summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_summary, alerts_summary)

        report = PerformanceReport(
            report_id=report_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            metrics_summary=metrics_summary,
            alerts_summary=alerts_summary,
            top_issues=top_issues,
            recommendations=recommendations,
        )

        logger.info(f"Generated report: {report_id}")

        return report

    def _identify_issues(
        self,
        metrics_summary: Dict[str, Any],
        alerts_summary: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify top performance issues"""
        issues = []

        # CPU issues
        if "cpu" in metrics_summary:
            cpu = metrics_summary["cpu"]
            if cpu["max"] > 90:
                issues.append({
                    "title": "Critical CPU Usage",
                    "description": f"CPU usage peaked at {cpu['max']}%",
                    "severity": "critical",
                })
            elif cpu["avg"] > 70:
                issues.append({
                    "title": "High CPU Usage",
                    "description": f"Average CPU usage is {cpu['avg']}%",
                    "severity": "warning",
                })

        # Memory issues
        if "memory" in metrics_summary:
            mem = metrics_summary["memory"]
            if mem["max"] > 90:
                issues.append({
                    "title": "Critical Memory Usage",
                    "description": f"Memory usage peaked at {mem['max']}%",
                    "severity": "critical",
                })
            elif mem["avg"] > 75:
                issues.append({
                    "title": "High Memory Usage",
                    "description": f"Average memory usage is {mem['avg']}%",
                    "severity": "warning",
                })

        # Alert issues
        if alerts_summary.get("active_alerts", 0) > 0:
            issues.append({
                "title": "Active Alerts",
                "description": f"{alerts_summary['active_alerts']} alerts are currently active",
                "severity": "warning",
            })

        # Throughput issues
        if "throughput" in metrics_summary:
            tp = metrics_summary["throughput"]
            if tp["avg"] < 1.0 and tp["avg"] > 0:
                issues.append({
                    "title": "Low Message Throughput",
                    "description": f"Average throughput is only {tp['avg']} msg/s",
                    "severity": "info",
                })

        # Sort by severity and limit
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return issues[:5]

    def _generate_recommendations(
        self,
        metrics_summary: Dict[str, Any],
        alerts_summary: Dict[str, Any],
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # CPU recommendations
        if "cpu" in metrics_summary:
            cpu = metrics_summary["cpu"]
            if cpu["avg"] > 70:
                recommendations.append("Consider optimizing CPU-intensive operations or scaling up")
            if cpu["max"] > 90:
                recommendations.append("Investigate CPU spikes and optimize resource usage")

        # Memory recommendations
        if "memory" in metrics_summary:
            mem = metrics_summary["memory"]
            if mem["avg"] > 75:
                recommendations.append("Monitor memory usage and implement memory optimization")
            if mem["max"] > 90:
                recommendations.append("Critical: Check for memory leaks and optimize memory allocation")

        # Alert recommendations
        if alerts_summary.get("active_alerts", 0) > 5:
            recommendations.append("Multiple alerts active - review and resolve system issues")

        # Throughput recommendations
        if "throughput" in metrics_summary:
            tp = metrics_summary["throughput"]
            if tp["avg"] < 1.0:
                recommendations.append("Low throughput detected - check agent activity and message flow")

        # General recommendations
        if not recommendations:
            recommendations.append("System performance is healthy - continue monitoring")

        return recommendations

    def save_report(
        self,
        report: PerformanceReport,
        format: str = "json",
    ) -> str:
        """
        Save report to file

        Args:
            report: PerformanceReport to save
            format: Output format (json or markdown)

        Returns:
            File path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            file_path = self.output_dir / f"{report.report_id}.md"
            with open(file_path, 'w') as f:
                f.write(report.to_markdown())
        else:
            file_path = self.output_dir / f"{report.report_id}.json"
            with open(file_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)

        logger.info(f"Saved report to {file_path}")
        return str(file_path)

    def get_latest_report(self) -> Optional[PerformanceReport]:
        """Get the most recent report"""
        report_files = sorted(self.output_dir.glob("report_*.json"), reverse=True)

        if report_files:
            try:
                with open(report_files[0], 'r') as f:
                    data = json.load(f)
                    return PerformanceReport(**data)
            except Exception as e:
                logger.error(f"Failed to load latest report: {e}")

        return None
