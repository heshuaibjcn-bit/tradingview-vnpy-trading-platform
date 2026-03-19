"""
Performance Stress Testing Suite

This module implements comprehensive performance testing tools:
- Load generation
- Performance benchmarking
- Memory leak detection
- Stability testing
"""

import asyncio
import time
import psutil
import tracemalloc
import gc
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import statistics
import sys


@dataclass
class PerformanceMetrics:
    """Performance metrics from a test run"""
    test_name: str
    start_time: float
    end_time: float
    duration: float = 0

    # Operation metrics
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

    # Timing metrics
    operation_times: List[float] = field(default_factory=list)

    # Resource metrics
    cpu_samples: List[float] = field(default_factory=list)
    memory_samples: List[int] = field(default_factory=list)

    # Errors
    errors: List[str] = field(default_factory=list)

    def get_throughput(self) -> float:
        """Get operations per second"""
        if self.duration > 0:
            return self.total_operations / self.duration
        return 0.0

    def get_avg_latency(self) -> float:
        """Get average operation latency"""
        if self.operation_times:
            return statistics.mean(self.operation_times)
        return 0.0

    def get_p95_latency(self) -> float:
        """Get 95th percentile latency"""
        if self.operation_times:
            return statistics.quantiles(self.operation_times, n=20)[18]  # 95th percentile
        return 0.0

    def get_p99_latency(self) -> float:
        """Get 99th percentile latency"""
        if self.operation_times:
            return statistics.quantiles(self.operation_times, n=100)[98]  # 99th percentile
        return 0.0

    def get_avg_cpu(self) -> float:
        """Get average CPU usage"""
        if self.cpu_samples:
            return statistics.mean(self.cpu_samples)
        return 0.0

    def get_max_memory(self) -> int:
        """Get peak memory usage"""
        if self.memory_samples:
            return max(self.memory_samples)
        return 0

    def get_memory_leak_indicator(self) -> float:
        """Get memory leak indicator (MB/min)"""
        if len(self.memory_samples) < 2:
            return 0.0

        # Simple linear regression slope
        n = len(self.memory_samples)
        x = list(range(n))
        y = self.memory_samples

        # Calculate slope (memory growth rate)
        slope = (n * sum(xi * yi for xi, yi in zip(x, y)) - sum(x) * sum(y)) / \
                (n * sum(xi ** 2 for xi in x) - sum(x) ** 2)

        # Convert bytes/minute to MB/minute
        return (slope * 60) / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_name": self.test_name,
            "duration": self.duration,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": self.successful_operations / max(self.total_operations, 1),
            "throughput_ops": self.get_throughput(),
            "avg_latency_ms": self.get_avg_latency() * 1000,
            "p95_latency_ms": self.get_p95_latency() * 1000,
            "p99_latency_ms": self.get_p99_latency() * 1000,
            "avg_cpu_percent": self.get_avg_cpu(),
            "max_memory_mb": self.get_max_memory() / (1024 * 1024),
            "memory_leak_mb_per_min": self.get_memory_leak_indicator(),
            "error_count": len(self.errors),
        }


class LoadGenerator:
    """
    Generates load for performance testing

    Features:
    - Configurable request rate
    - Multiple worker patterns
    - Realistic traffic patterns
    """

    def __init__(
        self,
        target_func: Callable,
        max_workers: int = 100,
        ramp_up_time: float = 10.0,
    ):
        """
        Initialize load generator

        Args:
            target_func: Function to execute (async or sync)
            max_workers: Maximum concurrent workers
            ramp_up_time: Time to reach full load
        """
        self.target_func = target_func
        self.max_workers = max_workers
        self.ramp_up_time = ramp_up_time

        self._running = False
        self._active_tasks: Set[asyncio.Task] = set()

    async def start_constant_load(
        self,
        requests_per_second: float,
        duration: float,
    ) -> PerformanceMetrics:
        """
        Generate constant load

        Args:
            requests_per_second: Target request rate
            duration: Test duration

        Returns:
            Performance metrics
        """
        metrics = PerformanceMetrics(
            test_name="constant_load",
            start_time=time.time(),
        )

        self._running = True

        # Calculate interval between requests
        interval = 1.0 / requests_per_second

        logger.info(
            f"Starting constant load test: "
            f"{requests_per_second} req/s for {duration}s"
        )

        # Start monitoring
        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            end_time = time.time() + duration

            while time.time() < end_time and self._running:
                start = time.time()

                # Execute operation
                try:
                    if asyncio.iscoroutinefunction(self.target_func):
                        await self.target_func()
                    else:
                        self.target_func()

                    metrics.successful_operations += 1
                except Exception as e:
                    metrics.failed_operations += 1
                    metrics.errors.append(str(e))

                metrics.total_operations += 1
                op_time = time.time() - start
                metrics.operation_times.append(op_time)

                # Maintain request rate
                elapsed = time.time() - start
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)

        finally:
            self._running = False
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time

        logger.info(
            f"Load test complete: "
            f"{metrics.total_operations} ops, "
            f"{metrics.get_throughput():.0f} ops/s"
        )

        return metrics

    async def start_spike_load(
        self,
        baseline_rps: float,
        spike_rps: float,
        spike_duration: float,
        total_duration: float,
    ) -> PerformanceMetrics:
        """
        Generate spike load (sudden increase in traffic)

        Args:
            baseline_rps: Baseline request rate
            spike_rps: Peak request rate during spike
            spike_duration: Duration of spike
            total_duration: Total test duration

        Returns:
            Performance metrics
        """
        metrics = PerformanceMetrics(
            test_name="spike_load",
            start_time=time.time(),
        )

        self._running = True

        logger.info(
            f"Starting spike load test: "
            f"{baseline_rps} -> {spike_rps} rps for {spike_duration}s"
        )

        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            end_time = time.time() + total_duration
            spike_end_time = time.time() + spike_duration

            while time.time() < end_time and self._running:
                # Determine current target rate
                if time.time() < spike_end_time:
                    current_rps = spike_rps
                else:
                    current_rps = baseline_rps

                interval = 1.0 / current_rps

                start = time.time()

                try:
                    if asyncio.iscoroutinefunction(self.target_func):
                        await self.target_func()
                    else:
                        self.target_func()

                    metrics.successful_operations += 1
                except Exception as e:
                    metrics.failed_operations += 1
                    metrics.errors.append(str(e))

                metrics.total_operations += 1
                op_time = time.time() - start
                metrics.operation_times.append(op_time)

                elapsed = time.time() - start
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)

        finally:
            self._running = False
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time

        return metrics

    async def _monitor_resources(self, metrics: PerformanceMetrics) -> None:
        """Monitor system resources during test"""
        process = psutil.Process()

        while self._running:
            try:
                # CPU usage
                cpu = process.cpu_percent(interval=0.1)
                metrics.cpu_samples.append(cpu)

                # Memory usage
                memory = process.memory_info().rss
                metrics.memory_samples.append(memory)

                await asyncio.sleep(0.5)  # Sample every 500ms

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

    def stop(self) -> None:
        """Stop load generation"""
        self._running = False


class StressTestSuite:
    """
    Comprehensive stress testing suite

    Tests:
    - Message throughput
    - Agent scalability
    - Memory efficiency
    - CPU efficiency
    - Stability under load
    """

    def __init__(self, save_results: bool = True):
        """
        Initialize stress test suite

        Args:
            save_results: Whether to save test results
        """
        self.save_results = save_results
        self.results: List[PerformanceMetrics] = []

    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all stress tests

        Returns:
            Test results summary
        """
        logger.info("Starting stress test suite...")

        results = []

        # Test 1: Message throughput
        logger.info("Running message throughput test...")
        results.append(await self.test_message_throughput())

        # Test 2: Agent scalability
        logger.info("Running agent scalability test...")
        results.append(await self.test_agent_scalability())

        # Test 3: Memory efficiency
        logger.info("Running memory efficiency test...")
        results.append(await self.test_memory_efficiency())

        # Test 4: CPU efficiency
        logger.info("Running CPU efficiency test...")
        results.append(await self.test_cpu_efficiency())

        # Test 5: Stability test
        logger.info("Running stability test...")
        results.append(await self.test_stability())

        # Generate summary
        summary = self._generate_summary(results)

        if self.save_results:
            self._save_results(results, summary)

        return summary

    async def test_message_throughput(self) -> PerformanceMetrics:
        """Test message throughput under load"""
        from agents import get_global_cache_manager
        from agents.messages import create_message, MessageType

        cache = get_global_cache_manager()
        market_cache = cache.get_cache("market_data")

        async def send_message():
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": "600000", "price": 10.0},
            )
            if market_cache:
                market_cache.set("test:key", {"data": "test"})

        generator = LoadGenerator(send_message, max_workers=50)
        metrics = await generator.start_constant_load(
            requests_per_second=1000,
            duration=10.0,
        )

        logger.info(f"✅ Throughput test: {metrics.get_throughput():.0f} msg/s")
        return metrics

    async def test_agent_scalability(self) -> PerformanceMetrics:
        """Test system scalability with increasing load"""
        from agents import get_global_cache_manager

        cache = get_global_cache_manager()

        async def cache_operation():
            market_cache = cache.get_cache("market_data")
            if market_cache:
                # Simulate cache operations
                for i in range(10):
                    market_cache.set(f"key{i}", f"value{i}")
                    market_cache.get(f"key{i}")

        generator = LoadGenerator(cache_operation, max_workers=100)

        # Ramp up load
        metrics = PerformanceMetrics(
            test_name="agent_scalability",
            start_time=time.time(),
        )

        self._running = True
        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            # Start with 100 ops/s, ramp to 1000 ops/s
            rates = [100, 250, 500, 750, 1000]
            duration_per_rate = 5.0

            for rate in rates:
                logger.info(f"Testing at {rate} ops/s...")
                rate_metrics = await generator.start_constant_load(rate, duration_per_rate)

                # Aggregate metrics
                metrics.total_operations += rate_metrics.total_operations
                metrics.successful_operations += rate_metrics.successful_operations
                metrics.failed_operations += rate_metrics.failed_operations
                metrics.operation_times.extend(rate_metrics.operation_times)

        finally:
            self._running = False
            monitor_task.cancel()

        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time

        logger.info(f"✅ Scalability test: {metrics.get_throughput():.0f} avg ops/s")
        return metrics

    async def test_memory_efficiency(self) -> PerformanceMetrics:
        """Test memory efficiency and detect leaks"""
        # Start memory tracing
        tracemalloc.start()

        # Force garbage collection
        gc.collect()

        from agents import get_global_cache_manager
        cache = get_global_cache_manager()

        async def memory_intensive_operation():
            market_cache = cache.get_cache("market_data")
            if market_cache:
                # Add many entries
                for i in range(1000):
                    market_cache.set(f"mem_test_{i}", "x" * 1000)

                # Read entries
                for i in range(1000):
                    market_cache.get(f"mem_test_{i}")

                # Cleanup
                for i in range(1000):
                    market_cache.delete(f"mem_test_{i}")

        metrics = PerformanceMetrics(
            test_name="memory_efficiency",
            start_time=time.time(),
        )

        generator = LoadGenerator(memory_intensive_operation)
        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            # Run for 30 seconds
            await generator.start_constant_load(
                requests_per_second=50,
                duration=30.0,
            )

            # Get memory snapshot
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')

            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time

            # Check for memory leaks
            leak_rate = metrics.get_memory_leak_indicator()

            logger.info(
                f"✅ Memory test: "
                f"max={metrics.get_max_memory() / (1024*1024):.1f}MB, "
                f"leak_rate={leak_rate:.2f}MB/min"
            )

            tracemalloc.stop()

        finally:
            monitor_task.cancel()

        return metrics

    async def test_cpu_efficiency(self) -> PerformanceMetrics:
        """Test CPU efficiency"""
        from agents import get_global_cache_manager
        cache = get_global_cache_manager()

        async def cpu_intensive_operation():
            # Simulate calculations
            result = 0
            for i in range(1000):
                result += i ** 2
            return result

        metrics = PerformanceMetrics(
            test_name="cpu_efficiency",
            start_time=time.time(),
        )

        generator = LoadGenerator(cpu_intensive_operation)
        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            await generator.start_constant_load(
                requests_per_second=100,
                duration=10.0,
            )

            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time

            logger.info(
                f"✅ CPU test: "
                f"avg_cpu={metrics.get_avg_cpu():.1f}%, "
                f"throughput={metrics.get_throughput():.0f} ops/s"
            )

        finally:
            monitor_task.cancel()

        return metrics

    async def test_stability(self) -> PerformanceMetrics:
        """Test long-running stability"""
        from agents import get_global_cache_manager
        cache = get_global_cache_manager()

        async def normal_operation():
            market_cache = cache.get_cache("market_data")
            strategy_cache = cache.get_cache("strategy_results")

            if market_cache:
                market_cache.set("stability_test", time.time())
                market_cache.get("stability_test")

            if strategy_cache:
                strategy_cache.set("test_result", {"value": 42})
                strategy_cache.get("test_result")

            await asyncio.sleep(0.001)

        metrics = PerformanceMetrics(
            test_name="stability",
            start_time=time.time(),
        )

        generator = LoadGenerator(normal_operation)
        monitor_task = asyncio.create_task(self._monitor_resources(metrics))

        try:
            # Run for 5 minutes
            logger.info("Running 5-minute stability test...")
            await generator.start_constant_load(
                requests_per_second=100,
                duration=300.0,  # 5 minutes
            )

            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time

            logger.info(
                f"✅ Stability test: "
                f"{metrics.total_operations} ops, "
                f"{metrics.failed_operations} errors, "
                f"{metrics.get_throughput():.0f} ops/s"
            )

        finally:
            monitor_task.cancel()

        return metrics

    async def _monitor_resources(self, metrics: PerformanceMetrics) -> None:
        """Monitor system resources"""
        process = psutil.Process()

        while getattr(self, '_running', False):
            try:
                cpu = process.cpu_percent(interval=0.1)
                metrics.cpu_samples.append(cpu)

                memory = process.memory_info().rss
                metrics.memory_samples.append(memory)

                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(1.0)

    def _generate_summary(self, results: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "tests": [],
        }

        for metrics in results:
            summary["tests"].append(metrics.to_dict())

        # Overall stats
        total_ops = sum(m.total_operations for m in results)
        total_errors = sum(m.failed_operations for m in results)
        avg_cpu = statistics.mean([m.get_avg_cpu() for m in results if m.cpu_samples])
        max_memory = max(m.get_max_memory() for m in results)

        summary["overall"] = {
            "total_operations": total_ops,
            "total_errors": total_errors,
            "error_rate": total_errors / max(total_ops, 1),
            "avg_cpu_percent": avg_cpu,
            "max_memory_mb": max_memory / (1024 * 1024),
        }

        return summary

    def _save_results(self, results: List[PerformanceMetrics], summary: Dict[str, Any]) -> None:
        """Save test results to file"""
        from pathlib import Path

        output_dir = Path("data/performance_tests")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save summary
        summary_file = output_dir / f"stress_test_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        # Save detailed results
        results_file = output_dir / f"stress_test_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump([r.to_dict() for r in results], f, indent=2)

        logger.info(f"✅ Results saved to {output_dir}")


# Convenience functions
async def run_quick_stress_test() -> Dict[str, Any]:
    """Run a quick stress test (1 minute)"""
    suite = StressTestSuite(save_results=True)

    # Quick test: just throughput
    logger.info("Running quick stress test...")
    result = await suite.test_message_throughput()

    return {
        "quick_test": result.to_dict(),
        "timestamp": datetime.now().isoformat(),
    }


async def run_full_stress_test() -> Dict[str, Any]:
    """Run full stress test suite"""
    suite = StressTestSuite(save_results=True)
    return await suite.run_all_tests()
