"""
Unit tests for async task scheduler
"""

import asyncio
import pytest
import time
from pytest_asyncio import fixture

from agents.async_scheduler import (
    TaskPriority,
    PrioritizedTask,
    ConcurrencyConfig,
    SchedulerStats,
    AsyncTaskScheduler,
    AgentConcurrencyManager,
)


class TestTaskPriority:
    """Test TaskPriority enum"""

    def test_priority_order(self):
        """Test that priority values are ordered correctly"""
        assert TaskPriority.CRITICAL < TaskPriority.HIGH
        assert TaskPriority.HIGH < TaskPriority.NORMAL
        assert TaskPriority.NORMAL < TaskPriority.LOW
        assert TaskPriority.LOW < TaskPriority.IDLE


class TestConcurrencyConfig:
    """Test ConcurrencyConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ConcurrencyConfig()

        assert config.max_concurrent_tasks == 100
        assert config.max_queue_size == 1000
        assert config.task_timeout == 30.0
        assert config.queue_timeout == 5.0
        assert config.enable_priorities is True
        assert config.enable_monitoring is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = ConcurrencyConfig(
            max_concurrent_tasks=50,
            max_queue_size=500,
            task_timeout=60.0,
            enable_priorities=False,
        )

        assert config.max_concurrent_tasks == 50
        assert config.max_queue_size == 500
        assert config.task_timeout == 60.0
        assert config.enable_priorities is False


class TestSchedulerStats:
    """Test SchedulerStats"""

    def test_default_stats(self):
        """Test default statistics values"""
        stats = SchedulerStats()

        assert stats.tasks_submitted == 0
        assert stats.tasks_completed == 0
        assert stats.tasks_failed == 0
        assert stats.tasks_cancelled == 0
        assert stats.tasks_timeout == 0

    def test_stats_to_dict(self):
        """Test converting stats to dictionary"""
        stats = SchedulerStats()
        stats.tasks_submitted = 100
        stats.tasks_completed = 95
        stats.tasks_failed = 3

        data = stats.to_dict()

        assert data["tasks_submitted"] == 100
        assert data["tasks_completed"] == 95
        assert data["tasks_failed"] == 3
        assert "success_rate" in data
        assert data["success_rate"] == 0.95

    def test_stats_reset(self):
        """Test resetting statistics"""
        stats = SchedulerStats()
        stats.tasks_submitted = 100
        stats.tasks_completed = 95

        stats.reset()

        assert stats.tasks_submitted == 0
        assert stats.tasks_completed == 0


class TestAsyncTaskScheduler:
    """Test AsyncTaskScheduler"""

    @fixture
    async def scheduler(self):
        """Create a test scheduler"""
        config = ConcurrencyConfig(
            max_concurrent_tasks=5,
            max_queue_size=50,
            task_timeout=10.0,
            enable_monitoring=False,  # Disable for tests
        )

        scheduler = AsyncTaskScheduler(config)
        await scheduler.start()

        yield scheduler

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping scheduler"""
        scheduler = AsyncTaskScheduler(enable_monitoring=False)

        assert not scheduler.is_running

        await scheduler.start()
        assert scheduler.is_running

        await scheduler.stop()
        assert not scheduler.is_running

    @pytest.mark.asyncio
    async def test_submit_task(self, scheduler):
        """Test submitting a task"""
        executed = []

        async def test_task():
            executed.append(1)
            await asyncio.sleep(0.1)

        task_id = await scheduler.submit(test_task, priority=TaskPriority.NORMAL)

        assert task_id is not None

        # Wait for task to complete
        await asyncio.sleep(0.3)

        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_priority_execution(self, scheduler):
        """Test that higher priority tasks execute first"""
        execution_order = []

        async def low_priority_task():
            execution_order.append("low")

        async def high_priority_task():
            execution_order.append("high")

        # Submit low priority first
        await scheduler.submit(
            low_priority_task,
            priority=TaskPriority.LOW,
            task_id="low_task",
        )

        # Submit high priority
        await scheduler.submit(
            high_priority_task,
            priority=TaskPriority.HIGH,
            task_id="high_task",
        )

        # Wait for both to complete
        await asyncio.sleep(0.5)

        # High priority should execute first
        assert execution_order[0] == "high"

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, scheduler):
        """Test that concurrency limit is enforced"""
        running_count = [0]
        max_concurrent = [0]

        async def test_task():
            running_count[0] += 1
            max_concurrent[0] = max(max_concurrent[0], running_count[0])
            await asyncio.sleep(0.2)
            running_count[0] -= 1

        # Submit more tasks than concurrency limit
        tasks = []
        for i in range(10):
            task_id = await scheduler.submit(
                test_task,
                priority=TaskPriority.NORMAL,
                task_id=f"task_{i}",
            )
            tasks.append(task_id)

        # Wait for all to complete
        await asyncio.sleep(1.0)

        # Should not exceed concurrency limit
        assert max_concurrent[0] <= scheduler.config.max_concurrent_tasks

    @pytest.mark.asyncio
    async def test_task_timeout(self, scheduler):
        """Test that tasks timeout correctly"""
        config = ConcurrencyConfig(
            max_concurrent_tasks=5,
            max_queue_size=50,
            task_timeout=0.1,  # Short timeout
            enable_monitoring=False,
        )

        scheduler = AsyncTaskScheduler(config)
        await scheduler.start()

        async def slow_task():
            await asyncio.sleep(1.0)  # Longer than timeout

        task_id = await scheduler.submit(slow_task)

        # Wait for timeout
        await asyncio.sleep(0.3)

        stats = scheduler.get_stats()
        assert stats['tasks_timeout'] > 0

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_task_cancellation(self, scheduler):
        """Test task cancellation"""
        started = False

        async def cancellable_task():
            nonlocal started
            started = True
            await asyncio.sleep(1.0)

        task_id = await scheduler.submit(
            cancellable_task,
            task_id="cancellable_task",
        )

        # Small delay to let task start
        await asyncio.sleep(0.1)

        # Cancel the task
        cancelled = await scheduler.cancel(task_id)

        assert cancelled is True

    @pytest.mark.asyncio
    async def test_queue_full(self, scheduler):
        """Test that queue rejects tasks when full"""
        # Create scheduler with small queue
        config = ConcurrencyConfig(
            max_concurrent_tasks=1,
            max_queue_size=2,
            task_timeout=10.0,
            enable_monitoring=False,
        )

        scheduler = AsyncTaskScheduler(config)
        await scheduler.start()

        async def blocking_task():
            await asyncio.sleep(1.0)

        async def quick_task():
            await asyncio.sleep(0.01)

        # Submit blocking task
        await scheduler.submit(blocking_task, task_id="blocking")

        # Fill queue
        await scheduler.submit(quick_task, task_id="task1")
        await scheduler.submit(quick_task, task_id="task2")

        # This should fail - queue is full
        with pytest.raises(asyncio.QueueFull):
            await scheduler.submit(quick_task, task_id="task3")

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self, scheduler):
        """Test getting scheduler statistics"""
        async def test_task():
            await asyncio.sleep(0.01)

        # Submit some tasks
        for i in range(5):
            await scheduler.submit(test_task, task_id=f"task_{i}")

        # Wait for completion
        await asyncio.sleep(0.3)

        stats = scheduler.get_stats()

        assert stats['tasks_submitted'] == 5
        assert stats['tasks_completed'] > 0

    @pytest.mark.asyncio
    async def test_reset_stats(self, scheduler):
        """Test resetting statistics"""
        async def test_task():
            await asyncio.sleep(0.01)

        await scheduler.submit(test_task)

        # Wait for completion
        await asyncio.sleep(0.2)

        scheduler.reset_stats()

        stats = scheduler.get_stats()
        assert stats['tasks_submitted'] == 0


class TestAgentConcurrencyManager:
    """Test AgentConcurrencyManager"""

    @pytest.mark.asyncio
    async def test_acquire_release_slot(self):
        """Test acquiring and releasing agent slots"""
        manager = AgentConcurrencyManager(
            max_concurrent_per_agent=2,
            max_messages_per_second=100,
        )

        # Acquire slots
        assert await manager.acquire_agent_slot("agent1") is True
        assert await manager.acquire_agent_slot("agent1") is True
        assert await manager.acquire_agent_slot("agent1") is True  # Should still work with semaphore

        # Release slots
        manager.release_agent_slot("agent1")
        manager.release_agent_slot("agent1")

        stats = manager.get_stats()
        assert stats['total_messages_sent'] > 0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test message rate limiting"""
        manager = AgentConcurrencyManager(
            max_concurrent_per_agent=10,
            max_messages_per_second=10,  # 10 messages per second
        )

        # Send 10 messages (should all pass)
        passed = 0
        for i in range(10):
            if await manager.check_rate_limit("agent1"):
                passed += 1

        assert passed == 10

        # Next message should be rate limited
        assert await manager.check_rate_limit("agent1") is False

        # Wait for rate limit to reset
        await asyncio.sleep(1.1)

        # Should work again
        assert await manager.check_rate_limit("agent1") is True

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting concurrency manager statistics"""
        manager = AgentConcurrencyManager(
            max_concurrent_per_agent=5,
            max_messages_per_second=100,
        )

        await manager.acquire_agent_slot("agent1")
        await manager.acquire_agent_slot("agent2")

        stats = manager.get_stats()

        assert stats['total_messages_sent'] == 2
        assert stats['total_throttled'] == 0
        assert 'throttle_rate' in stats


class TestSchedulerPerformance:
    """Performance tests for async scheduler"""

    @pytest.mark.asyncio
    async def test_throughput(self):
        """Test scheduler throughput"""
        completed = [0]

        async def test_task():
            completed[0] += 1
            await asyncio.sleep(0.01)

        config = ConcurrencyConfig(
            max_concurrent_tasks=50,
            max_queue_size=1000,
            task_timeout=10.0,
            enable_monitoring=False,
        )

        scheduler = AsyncTaskScheduler(config)
        await scheduler.start()

        start_time = time.time()

        # Submit 100 tasks
        for i in range(100):
            await scheduler.submit(
                test_task,
                task_id=f"task_{i}",
                priority=TaskPriority.NORMAL,
            )

        # Wait for all to complete
        await asyncio.sleep(3.0)

        elapsed = time.time() - start_time

        await scheduler.stop()

        assert completed[0] == 100
        throughput = completed[0] / elapsed
        print(f"Scheduler throughput: {throughput:.0f} tasks/second")

        # Should process at least 30 tasks/second
        assert throughput > 30

    @pytest.mark.asyncio
    async def test_priority_latency(self):
        """Test latency difference between priorities"""
        high_latency = []
        low_latency = []

        async def high_priority_task():
            high_latency.append(time.time())
            await asyncio.sleep(0.01)

        async def low_priority_task():
            low_latency.append(time.time())
            await asyncio.sleep(0.01)

        config = ConcurrencyConfig(
            max_concurrent_tasks=1,
            max_queue_size=100,
            task_timeout=10.0,
            enable_monitoring=False,
        )

        scheduler = AsyncTaskScheduler(config)
        await scheduler.start()

        # Submit low priority tasks first
        for i in range(5):
            await scheduler.submit(
                low_priority_task,
                task_id=f"low_{i}",
                priority=TaskPriority.LOW,
            )

        # Submit high priority task
        start_time = time.time()
        await scheduler.submit(
            high_priority_task,
            task_id="high_0",
            priority=TaskPriority.HIGH,
        )

        # Wait for completion
        await asyncio.sleep(0.5)

        await scheduler.stop()

        if high_latency:
            high_wait = (high_latency[0] - start_time) * 1000
            print(f"High priority latency: {high_wait:.2f}ms")

            # High priority should be processed relatively quickly
            assert high_wait < 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
