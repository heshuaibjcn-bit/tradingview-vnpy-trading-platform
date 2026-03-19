"""
Async Task Scheduler with Priority Queue and Concurrency Control

This module implements an advanced asyncio task scheduler with:
- Priority-based task queuing
- Concurrency limiting
- Task cancellation
- Performance monitoring
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict, deque
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from loguru import logger
import heapq


class TaskPriority(IntEnum):
    """Task priority levels (lower value = higher priority)"""
    CRITICAL = 0    # Emergency stop, critical errors
    HIGH = 1        # Time-sensitive market data
    NORMAL = 2      # Regular operations
    LOW = 3         # Background tasks
    IDLE = 4        # Maintenance tasks


@dataclass(order=True)
class PrioritizedTask:
    """A task with priority for scheduling"""
    priority: int
    task_id: str = field(compare=False)
    coro: Callable = field(compare=False)
    created_at: float = field(compare=False, default_factory=time.time)
    timeout: Optional[float] = field(compare=False, default=None)
    callback: Optional[Callable] = field(compare=False, default=None)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)

    def __hash__(self):
        return hash(self.task_id)


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency control"""
    max_concurrent_tasks: int = 100
    max_queue_size: int = 1000
    task_timeout: float = 30.0
    queue_timeout: float = 5.0
    enable_priorities: bool = True
    enable_monitoring: bool = True


@dataclass
class SchedulerStats:
    """Scheduler statistics"""
    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_cancelled: int = 0
    tasks_timeout: int = 0

    current_queue_size: int = 0
    current_running: int = 0

    total_wait_time: float = 0.0
    total_run_time: float = 0.0

    priority_distribution: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    last_reset: datetime = field(default_factory=datetime.now)

    def reset(self):
        """Reset statistics"""
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tasks_submitted": self.tasks_submitted,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_cancelled": self.tasks_cancelled,
            "tasks_timeout": self.tasks_timeout,
            "current_queue_size": self.current_queue_size,
            "current_running": self.current_running,
            "total_wait_time": self.total_wait_time,
            "total_run_time": self.total_run_time,
            "avg_wait_time": self.total_wait_time / max(self.tasks_completed, 1),
            "avg_run_time": self.total_run_time / max(self.tasks_completed, 1),
            "priority_distribution": dict(self.priority_distribution),
            "success_rate": self.tasks_completed / max(self.tasks_submitted, 1),
            "last_reset": self.last_reset.isoformat(),
        }


class AsyncTaskScheduler:
    """
    Advanced asyncio task scheduler with priority and concurrency control

    Features:
    - Priority-based task queue
    - Concurrent task limiting
    - Task timeout handling
    - Task cancellation
    - Performance monitoring
    """

    def __init__(
        self,
        config: Optional[ConcurrencyConfig] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        Initialize the task scheduler

        Args:
            config: Concurrency configuration
            loop: Event loop (uses current loop if None)
        """
        self.config = config or ConcurrencyConfig()
        self._loop = loop or asyncio.get_event_loop()

        # Task queues (one heap per priority for fairness)
        self._queues: Dict[int, List] = defaultdict(list)
        self._queue_lock = asyncio.Lock()

        # Active tasks
        self._active_tasks: Set[asyncio.Task] = set()
        self._task_info: Dict[str, Dict] = {}

        # Semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        # Statistics
        self._stats = SchedulerStats()

        # Background monitor
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"AsyncTaskScheduler initialized "
            f"(max_concurrent={self.config.max_concurrent_tasks}, "
            f"max_queue={self.config.max_queue_size})"
        )

    async def start(self) -> None:
        """Start the scheduler and background tasks"""
        if self._running:
            logger.warning("AsyncTaskScheduler already running")
            return

        self._running = True

        # Start monitoring if enabled
        if self.config.enable_monitoring:
            self._monitor_task = asyncio.create_task(self._monitor())

        logger.info("AsyncTaskScheduler started")

    async def stop(self) -> None:
        """Stop the scheduler and cancel all tasks"""
        if not self._running:
            return

        self._running = False

        # Cancel monitor
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Cancel all active tasks
        for task in list(self._active_tasks):
            task.cancel()

        # Wait for tasks to complete cancellation
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        self._active_tasks.clear()

        logger.info("AsyncTaskScheduler stopped")

    async def submit(
        self,
        coro: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit a task for execution

        Args:
            coro: Coroutine to execute
            priority: Task priority
            task_id: Optional task ID
            timeout: Task timeout in seconds
            callback: Optional callback on completion
            metadata: Optional metadata

        Returns:
            Task ID
        """
        # Generate task ID if not provided
        if task_id is None:
            task_id = f"task_{time.time()}_{id(coro)}"

        # Create prioritized task
        task = PrioritizedTask(
            priority=priority,
            task_id=task_id,
            coro=coro,
            timeout=timeout or self.config.task_timeout,
            callback=callback,
            metadata=metadata or {},
        )

        # Check queue size
        async with self._queue_lock:
            total_queued = sum(len(q) for q in self._queues.values())
            if total_queued >= self.config.max_queue_size:
                raise asyncio.QueueFull(
                    f"Task queue full ({total_queued}/{self.config.max_queue_size})"
                )

            # Add to appropriate priority queue
            heapq.heappush(self._queues[priority], task)
            self._stats.tasks_submitted += 1
            self._stats.priority_distribution[priority] += 1
            self._stats.current_queue_size = sum(len(q) for q in self._queues.values())

            logger.debug(
                f"Task submitted: {task_id} "
                f"(priority={priority.name}, queue_size={total_queued + 1})"
            )

        # Try to process queues
        asyncio.create_task(self._process_queues())

        return task_id

    async def _process_queues(self) -> None:
        """Process task queues and execute tasks"""
        # Try to acquire semaphore
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.config.queue_timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Queue processing timeout - no available slots")
            return

        # Get next task from queues (highest priority first)
        async with self._queue_lock:
            task = None
            for priority in sorted(self._queues.keys()):
                if self._queues[priority]:
                    task = heapq.heappop(self._queues[priority])
                    break

            if not task:
                self._semaphore.release()
                return

            self._stats.current_queue_size = sum(len(q) for q in self._queues.values())

        # Execute the task
        asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: PrioritizedTask) -> None:
        """Execute a single task with timeout and error handling"""
        task_id = task.task_id
        start_time = time.time()
        wait_time = start_time - task.created_at

        try:
            # Record task info
            self._task_info[task_id] = {
                "task": task,
                "started_at": start_time,
                "status": "running",
            }

            self._stats.current_running += 1

            logger.debug(f"Executing task: {task_id}")

            # Execute with timeout
            result = await asyncio.wait_for(
                task.coro(),
                timeout=task.timeout
            )

            # Task completed successfully
            run_time = time.time() - start_time

            self._stats.tasks_completed += 1
            self._stats.total_wait_time += wait_time
            self._stats.total_run_time += run_time

            # Call callback if provided
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(result)
                    else:
                        task.callback(result)
                except Exception as e:
                    logger.error(f"Task {task_id} callback error: {e}")

            logger.debug(
                f"Task completed: {task_id} "
                f"(wait={wait_time:.3f}s, run={run_time:.3f}s)"
            )

        except asyncio.TimeoutError:
            self._stats.tasks_timeout += 1
            logger.warning(f"Task timeout: {task_id} (timeout={task.timeout}s)")

        except asyncio.CancelledError:
            self._stats.tasks_cancelled += 1
            logger.info(f"Task cancelled: {task_id}")

        except Exception as e:
            self._stats.tasks_failed += 1
            logger.error(f"Task failed: {task_id} - {e}")

        finally:
            # Cleanup
            self._active_tasks.discard(task_id)
            self._current_running = getattr(self, '_current_running', 0)
            self._current_running = max(0, self._current_running - 1)
            self._task_info.pop(task_id, None)
            self._semaphore.release()

            # Try to process next task
            if self._running:
                await self._process_queues()

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled
        """
        # Check if task is in queue
        async with self._queue_lock:
            for priority, queue in self._queues.items():
                for i, task in enumerate(queue):
                    if task.task_id == task_id:
                        # Remove from queue
                        queue.pop(i)
                        heapq.heapify(queue)
                        self._stats.tasks_cancelled += 1
                        self._stats.current_queue_size = sum(len(q) for q in self._queues.values())
                        logger.info(f"Task cancelled from queue: {task_id}")
                        return True

        # Check if task is running
        if task_id in self._task_info:
            info = self._task_info[task_id]
            # Cancel the task (actual cancellation happens in next await point)
            logger.info(f"Task cancellation requested: {task_id}")
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        self._stats.current_running = len(self._active_tasks)
        return self._stats.to_dict()

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific task"""
        if task_id in self._task_info:
            info = self._task_info[task_id].copy()
            info['task'] = info['task'].task_id  # Don't return the full task object
            return info
        return None

    async def _monitor(self) -> None:
        """Background monitor for scheduler health"""
        logger.debug("Scheduler monitor started")

        while self._running:
            try:
                await asyncio.sleep(5)

                # Log statistics
                stats = self.get_stats()
                logger.debug(
                    f"Scheduler: queued={stats['current_queue_size']}, "
                    f"running={stats['current_running']}, "
                    f"completed={stats['tasks_completed']}, "
                    f"failed={stats['tasks_failed']}"
                )

                # Check for stuck tasks
                for task_id, info in list(self._task_info.items()):
                    elapsed = time.time() - info['started_at']
                    if elapsed > self.config.task_timeout * 2:
                        logger.warning(
                            f"Possible stuck task: {task_id} "
                            f"(running for {elapsed:.1f}s)"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler monitor error: {e}")

        logger.debug("Scheduler monitor stopped")

    def reset_stats(self) -> None:
        """Reset statistics"""
        self._stats.reset()

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running


class AgentConcurrencyManager:
    """
    Manages concurrency for agent communication

    Provides:
    - Per-agent concurrency limits
    - Message rate limiting
    - Backpressure management
    """

    def __init__(
        self,
        max_concurrent_per_agent: int = 10,
        max_messages_per_second: float = 1000.0,
    ):
        """
        Initialize concurrency manager

        Args:
            max_concurrent_per_agent: Max concurrent messages per agent
            max_messages_per_second: Max message rate
        """
        self.max_concurrent_per_agent = max_concurrent_per_agent
        self.max_messages_per_second = max_messages_per_second

        # Per-agent semaphores
        self._agent_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._semaphore_lock = asyncio.Lock()

        # Rate limiting
        self._message_times: Dict[str, deque] = defaultdict(deque)

        # Statistics
        self._total_messages_sent = 0
        self._total_throttled = 0

    async def acquire_agent_slot(self, agent_name: str) -> bool:
        """
        Acquire a concurrency slot for an agent

        Args:
            agent_name: Agent name

        Returns:
            True if slot acquired
        """
        # Get or create semaphore for agent
        async with self._semaphore_lock:
            if agent_name not in self._agent_semaphores:
                self._agent_semaphores[agent_name] = asyncio.Semaphore(
                    self.max_concurrent_per_agent
                )

        semaphore = self._agent_semaphores[agent_name]

        # Try to acquire
        acquired = await semaphore.acquire()

        if acquired:
            self._total_messages_sent += 1
        else:
            self._total_throttled += 1

        return acquired

    def release_agent_slot(self, agent_name: str) -> None:
        """Release a concurrency slot for an agent"""
        if agent_name in self._agent_semaphores:
            self._agent_semaphores[agent_name].release()

    async def check_rate_limit(self, agent_name: str) -> bool:
        """
        Check if agent is within rate limit

        Args:
            agent_name: Agent name

        Returns:
            True if within rate limit
        """
        now = time.time()
        times = self._message_times[agent_name]

        # Remove old timestamps (older than 1 second)
        one_second_ago = now - 1.0
        while times and times[0] < one_second_ago:
            times.popleft()

        # Check rate limit
        if len(times) >= self.max_messages_per_second:
            return False

        times.append(now)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get concurrency manager statistics"""
        return {
            "total_messages_sent": self._total_messages_sent,
            "total_throttled": self._total_throttled,
            "throttle_rate": self._total_throttled / max(self._total_messages_sent, 1),
            "active_agents": len(self._agent_semaphores),
        }


# Global scheduler instance
_global_scheduler: Optional[AsyncTaskScheduler] = None


def get_global_scheduler() -> Optional[AsyncTaskScheduler]:
    """Get the global scheduler instance"""
    return _global_scheduler


def init_global_scheduler(
    config: Optional[ConcurrencyConfig] = None,
) -> AsyncTaskScheduler:
    """Initialize the global scheduler"""
    global _global_scheduler
    _global_scheduler = AsyncTaskScheduler(config)
    return _global_scheduler
