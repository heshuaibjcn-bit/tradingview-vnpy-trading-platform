"""
Performance Metrics Collector

Collects and stores system performance metrics for monitoring and analysis.
"""

import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger
import json

from config.settings import get_settings


@dataclass
class MetricPoint:
    """A single metric data point"""
    timestamp: str
    value: float
    tags: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """System performance metrics snapshot"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    message_count: int
    message_throughput: float  # messages per second
    active_agents: int
    healthy_agents: int
    unhealthy_agents: int
    total_messages: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """
    Collects system and application performance metrics
    """

    def __init__(
        self,
        collection_interval: float = 10.0,
        retention_hours: int = 24,
        storage_path: str = "data/metrics",
    ):
        """
        Initialize metrics collector

        Args:
            collection_interval: Seconds between metric collections
            retention_hours: Hours to keep metrics data
            storage_path: Path to store metrics data
        """
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._running = False
        self._collect_task = None

        # Metric storage (in-memory)
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history_size = int(retention_hours * 3600 / collection_interval)

        # Metric registries
        self._gauges: Dict[str, Callable[[], float]] = {}
        self._counters: Dict[str, float] = {}

        logger.info(
            f"MetricsCollector initialized "
            f"(interval={collection_interval}s, retention={retention_hours}h)"
        )

    def register_gauge(self, name: str, callback: Callable[[], float]) -> None:
        """
        Register a gauge metric (callback that returns current value)

        Args:
            name: Metric name
            callback: Function that returns current value
        """
        self._gauges[name] = callback
        logger.debug(f"Registered gauge metric: {name}")

    def register_counter(self, name: str, initial_value: float = 0.0) -> None:
        """
        Register a counter metric

        Args:
            name: Metric name
            initial_value: Initial counter value
        """
        self._counters[name] = initial_value
        logger.debug(f"Registered counter metric: {name} (initial={initial_value})")

    def increment_counter(self, name: str, delta: float = 1.0) -> None:
        """
        Increment a counter metric

        Args:
            name: Metric name
            delta: Amount to increment
        """
        if name in self._counters:
            self._counters[name] += delta

    def get_counter(self, name: str) -> float:
        """Get current counter value"""
        return self._counters.get(name, 0.0)

    def set_counter(self, name: str, value: float) -> None:
        """Set counter value"""
        if name in self._counters:
            self._counters[name] = value

    async def collect_system_metrics(self) -> PerformanceMetrics:
        """
        Collect current system performance metrics

        Returns:
            PerformanceMetrics snapshot
        """
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage('/')

            # Get message count from gauges
            message_count = self._gauges.get('message_count', lambda: 0)()

            # Calculate throughput (messages in last interval)
            throughput = 0.0
            if len(self._metrics_history) > 0:
                last_metrics = self._metrics_history[-1]
                time_diff = (datetime.now() - datetime.fromisoformat(last_metrics.timestamp)).total_seconds()
                msg_diff = message_count - last_metrics.message_count
                if time_diff > 0:
                    throughput = msg_diff / time_diff

            # Agent status
            active_agents = self._gauges.get('active_agents', lambda: 0)()
            healthy_agents = self._gauges.get('healthy_agents', lambda: 0)()
            unhealthy_agents = self._gauges.get('unhealthy_agents', lambda: 0)()

            # Total messages
            total_messages = self._gauges.get('total_messages', lambda: 0)()

            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_used_gb=disk.used / (1024 * 1024 * 1024),
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                message_count=int(message_count),
                message_throughput=round(throughput, 2),
                active_agents=int(active_agents),
                healthy_agents=int(healthy_agents),
                unhealthy_agents=int(unhealthy_agents),
                total_messages=int(total_messages),
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return empty metrics
            return PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                message_count=0,
                message_throughput=0.0,
                active_agents=0,
                healthy_agents=0,
                unhealthy_agents=0,
                total_messages=0,
            )

    async def _collect_loop(self) -> None:
        """Main collection loop"""
        while self._running:
            try:
                metrics = await self.collect_system_metrics()

                # Store in history
                self._metrics_history.append(metrics)

                # Trim history if needed
                if len(self._metrics_history) > self._max_history_size:
                    self._metrics_history = self._metrics_history[-self._max_history_size:]

                # Persist to disk periodically
                if len(self._metrics_history) % 10 == 0:
                    self._persist_metrics()

            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")

            # Wait for next collection
            await asyncio.sleep(self.collection_interval)

    def _persist_metrics(self) -> None:
        """Persist metrics to disk"""
        try:
            # Save latest metrics
            if self._metrics_history:
                latest = self._metrics_history[-1]
                timestamp = datetime.fromisoformat(latest.timestamp).strftime("%Y%m%d_%H%M%S")
                file_path = self.storage_path / f"metrics_{timestamp}.json"

                with open(file_path, 'w') as f:
                    json.dump([m.to_dict() for m in self._metrics_history[-60:]], f)

                # Clean old files
                self._cleanup_old_files()

        except Exception as e:
            logger.error(f"Failed to persist metrics: {e}")

    def _cleanup_old_files(self) -> None:
        """Clean up old metrics files"""
        try:
            cutoff = datetime.now() - timedelta(hours=self.retention_hours)

            for file_path in self.storage_path.glob("metrics_*.json"):
                # Extract timestamp from filename
                try:
                    timestamp_str = file_path.stem.split("_", 1)[1]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if file_time < cutoff:
                        file_path.unlink()
                        logger.debug(f"Deleted old metrics file: {file_path}")

                except (ValueError, IndexError):
                    continue

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics files: {e}")

    async def start(self) -> None:
        """Start metrics collection"""
        if self._running:
            logger.warning("Metrics collector already running")
            return

        self._running = True
        self._collect_task = asyncio.create_task(self._collect_loop())
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop metrics collection"""
        if not self._running:
            return

        self._running = False

        if self._collect_task:
            self._collect_task.cancel()
            try:
                await self._collect_task
            except asyncio.CancelledError:
                pass

        # Final persist
        self._persist_metrics()

        logger.info("Metrics collector stopped")

    def get_metrics_history(
        self,
        limit: int = 100,
    ) -> List[PerformanceMetrics]:
        """
        Get metrics history

        Args:
            limit: Maximum number of data points

        Returns:
            List of PerformanceMetrics
        """
        return self._metrics_history[-limit:]

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent metrics"""
        if self._metrics_history:
            return self._metrics_history[-1]
        return None

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary statistics"""
        if not self._metrics_history:
            return {}

        recent = self._metrics_history[-60:]  # Last hour (assuming 10s interval)

        cpu_values = [m.cpu_percent for m in recent]
        memory_values = [m.memory_percent for m in recent]
        throughput_values = [m.message_throughput for m in recent if m.message_throughput > 0]

        return {
            "period": "last_hour",
            "data_points": len(recent),
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2),
                "max": round(max(cpu_values), 2),
                "min": round(min(cpu_values), 2),
            },
            "memory": {
                "avg": round(sum(memory_values) / len(memory_values), 2),
                "max": round(max(memory_values), 2),
                "min": round(min(memory_values), 2),
            },
            "throughput": {
                "avg": round(sum(throughput_values) / len(throughput_values), 2) if throughput_values else 0,
                "max": round(max(throughput_values), 2) if throughput_values else 0,
                "current": recent[-1].message_throughput if recent else 0,
            },
            "agents": {
                "active": recent[-1].active_agents if recent else 0,
                "healthy": recent[-1].healthy_agents if recent else 0,
                "unhealthy": recent[-1].unhealthy_agents if recent else 0,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def load_persisted_metrics(self) -> None:
        """Load persisted metrics from disk"""
        try:
            metric_files = sorted(self.storage_path.glob("metrics_*.json"), reverse=True)

            for file_path in metric_files[:10]:  # Load last 10 files
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for metric_dict in data:
                        metrics = PerformanceMetrics(**metric_dict)
                        self._metrics_history.append(metrics)

            # Trim to max size
            if len(self._metrics_history) > self._max_history_size:
                self._metrics_history = self._metrics_history[-self._max_history_size:]

            logger.info(f"Loaded {len(self._metrics_history)} metrics from disk")

        except Exception as e:
            logger.error(f"Failed to load persisted metrics: {e}")


# Global metrics collector instance
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get global metrics collector instance"""
    return _collector


def init_metrics_collector(
    collection_interval: float = 10.0,
    retention_hours: int = 24,
    storage_path: str = "data/metrics",
) -> MetricsCollector:
    """
    Initialize global metrics collector

    Args:
        collection_interval: Seconds between collections
        retention_hours: Hours to keep metrics
        storage_path: Path to store metrics

    Returns:
        MetricsCollector instance
    """
    global _collector
    _collector = MetricsCollector(
        collection_interval=collection_interval,
        retention_hours=retention_hours,
        storage_path=storage_path,
    )
    return _collector
