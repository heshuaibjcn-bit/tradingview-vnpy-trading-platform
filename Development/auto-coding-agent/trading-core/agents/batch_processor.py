"""
Message Batch Processing System

This module implements batch processing for agent messages to improve
performance by reducing overhead when handling multiple messages.
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict, deque
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

from .messages import AgentMessage, MessageType
from .base import BaseAgent


@dataclass
class BatchConfig:
    """Configuration for batch processing"""

    # Maximum number of messages to accumulate before flushing
    max_batch_size: int = 100

    # Maximum time to wait before flushing (seconds)
    max_wait_time: float = 0.1

    # Whether to enable batch processing
    enabled: bool = True

    # Message types that should be processed immediately (not batched)
    immediate_types: Set[str] = field(default_factory=lambda: {
        MessageType.EMERGENCY_STOP,
        MessageType.ERROR,
        MessageType.HEALTH_CHECK,
    })

    # Maximum queue size before backpressure is applied
    max_queue_size: int = 10000

    def __post_init__(self):
        """Validate configuration"""
        if self.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        if self.max_wait_time <= 0:
            raise ValueError("max_wait_time must be positive")
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")


@dataclass
class BatchStats:
    """Statistics for batch processing"""

    messages_queued: int = 0
    messages_batched: int = 0
    messages_immediate: int = 0
    batches_processed: int = 0
    batches_flushed_by_size: int = 0
    batches_flushed_by_time: int = 0
    total_batch_time: float = 0.0
    avg_batch_size: float = 0.0
    avg_batch_latency: float = 0.0
    queue_overruns: int = 0

    # Time statistics
    min_batch_latency: float = float('inf')
    max_batch_latency: float = 0.0

    last_reset: datetime = field(default_factory=datetime.now)

    def reset(self):
        """Reset statistics"""
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "messages_queued": self.messages_queued,
            "messages_batched": self.messages_batched,
            "messages_immediate": self.messages_immediate,
            "batches_processed": self.batches_processed,
            "batches_flushed_by_size": self.batches_flushed_by_size,
            "batches_flushed_by_time": self.batches_flushed_by_time,
            "total_batch_time": self.total_batch_time,
            "avg_batch_size": self.avg_batch_size,
            "avg_batch_latency": self.avg_batch_latency,
            "queue_overruns": self.queue_overruns,
            "min_batch_latency": self.min_batch_latency if self.min_batch_latency != float('inf') else 0.0,
            "max_batch_latency": self.max_batch_latency,
            "last_reset": self.last_reset.isoformat(),
        }


class MessageBatcher:
    """
    Collects messages into batches for efficient processing

    Batches messages based on:
    - Maximum batch size
    - Maximum wait time
    - Message type (some types are processed immediately)
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        batch_processor: Optional[Callable[[List[AgentMessage]], Any]] = None,
    ):
        """
        Initialize message batcher

        Args:
            config: Batch configuration
            batch_processor: Function to process batches
        """
        self.config = config or BatchConfig()
        self._batch_processor = batch_processor

        # Message queue
        self._message_queue: deque[AgentMessage] = deque()

        # Queue management
        self._queue_lock = asyncio.Lock()
        self._queue_not_empty = asyncio.Condition(self._queue_lock)

        # Statistics
        self._stats = BatchStats()

        # Background task
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"MessageBatcher initialized "
            f"(batch_size={self.config.max_batch_size}, "
            f"wait_time={self.config.max_wait_time}s)"
        )

    async def start(self) -> None:
        """Start the batch processor"""
        if self._running:
            logger.warning("MessageBatcher already running")
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_batches())
        logger.info("MessageBatcher started")

    async def stop(self) -> None:
        """Stop the batch processor"""
        if not self._running:
            return

        self._running = False

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        # Flush remaining messages
        await self._flush()

        logger.info("MessageBatcher stopped")

    async def enqueue(self, message: AgentMessage) -> bool:
        """
        Enqueue a message for batch processing

        Args:
            message: Message to enqueue

        Returns:
            True if message was queued, False if queue is full
        """
        # Check if message should be processed immediately
        if message.msg_type in self.config.immediate_types:
            await self._process_immediate(message)
            self._stats.messages_immediate += 1
            return True

        # Check queue size
        async with self._queue_lock:
            if len(self._message_queue) >= self.config.max_queue_size:
                self._stats.queue_overruns += 1
                logger.warning(
                    f"Message queue full ({self.config.max_queue_size}), "
                    f"dropping message from {message.sender}"
                )
                return False

            self._message_queue.append(message)
            self._stats.messages_queued += 1

            # Notify processor
            self._queue_not_empty.notify()

        return True

    async def _process_immediate(self, message: AgentMessage) -> None:
        """Process an immediate message bypassing the batch"""
        if self._batch_processor:
            await self._batch_processor([message])
        else:
            logger.warning(f"No batch processor set for immediate message: {message.msg_type}")

    async def _process_batches(self) -> None:
        """Background task to process message batches"""
        logger.debug("Batch processor task started")

        while self._running:
            batch = await self._collect_batch()

            if batch:
                await self._process_batch(batch)

        logger.debug("Batch processor task stopped")

    async def _collect_batch(self) -> List[AgentMessage]:
        """
        Collect a batch of messages

        Returns:
            List of messages to process
        """
        batch_start = time.time()

        async with self._queue_not_empty:
            # Wait for messages
            while self._running and len(self._message_queue) == 0:
                try:
                    await asyncio.wait_for(
                        self._queue_not_empty.wait(),
                        timeout=self.config.max_wait_time
                    )
                except asyncio.TimeoutError:
                    # Timeout - return empty batch
                    return []

            if not self._running:
                return []

            # Collect messages
            batch_size = min(self.config.max_batch_size, len(self._message_queue))

            # Check if we should wait for more messages
            if len(self._message_queue) < self.config.max_batch_size:
                # Wait for more messages or timeout
                try:
                    await asyncio.wait_for(
                        self._queue_not_empty.wait(),
                        timeout=self.config.max_wait_time
                    )
                except asyncio.TimeoutError:
                    pass

                # Recalculate batch size
                batch_size = min(self.config.max_batch_size, len(self._message_queue))

            # Extract batch
            batch = []
            for _ in range(batch_size):
                if self._message_queue:
                    batch.append(self._message_queue.popleft())

            # Update statistics
            if batch:
                wait_time = time.time() - batch_start
                if len(batch) >= self.config.max_batch_size:
                    self._stats.batches_flushed_by_size += 1
                    logger.debug(f"Batch flushed by size: {len(batch)} messages, waited {wait_time:.3f}s")
                else:
                    self._stats.batches_flushed_by_time += 1
                    logger.debug(f"Batch flushed by time: {len(batch)} messages, waited {wait_time:.3f}s")

            return batch

    async def _process_batch(self, batch: List[AgentMessage]) -> None:
        """
        Process a batch of messages

        Args:
            batch: List of messages to process
        """
        if not batch:
            return

        batch_start = time.time()

        try:
            if self._batch_processor:
                # Process batch
                await self._batch_processor(batch)
            else:
                logger.warning(f"Received batch but no processor set: {len(batch)} messages")

            # Update statistics
            batch_time = time.time() - batch_start
            self._stats.batches_processed += 1
            self._stats.messages_batched += len(batch)
            self._stats.total_batch_time += batch_time

            # Update latency statistics
            if batch_time < self._stats.min_batch_latency:
                self._stats.min_batch_latency = batch_time
            if batch_time > self._stats.max_batch_latency:
                self._stats.max_batch_latency = batch_time

            # Update averages
            self._stats.avg_batch_size = (
                self._stats.messages_batched / self._stats.batches_processed
            )
            self._stats.avg_batch_latency = (
                self._stats.total_batch_time / self._stats.batches_processed
            )

            logger.debug(
                f"Processed batch of {len(batch)} messages in {batch_time:.3f}s "
                f"({len(batch)/batch_time:.0f} msg/s)"
            )

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Re-queue messages on error?
            # For now, we'll drop them to avoid infinite loops

    async def _flush(self) -> None:
        """Flush all remaining messages in the queue"""
        async with self._queue_lock:
            remaining = list(self._message_queue)
            self._message_queue.clear()

        if remaining:
            logger.info(f"Flushing {len(remaining)} remaining messages")
            await self._process_batch(remaining)

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return self._stats.to_dict()

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self._message_queue)

    def reset_stats(self) -> None:
        """Reset statistics"""
        self._stats.reset()


class BatchMessageBus:
    """
    Wrapper around AgentMessageBus to add batch processing support

    This class provides a drop-in replacement for AgentMessageBus with
    batch processing capabilities.
    """

    def __init__(
        self,
        message_bus: Any,  # AgentMessageBus instance
        batch_config: Optional[BatchConfig] = None,
    ):
        """
        Initialize batch message bus

        Args:
            message_bus: Underlying AgentMessageBus instance
            batch_config: Batch configuration
        """
        self._message_bus = message_bus
        self._batch_config = batch_config or BatchConfig()
        self._batcher: Optional[MessageBatcher] = None

        # Store original publish method
        self._original_publish = message_bus.publish

    async def start(self) -> None:
        """Start batch processing"""
        if not self._batch_config.enabled:
            logger.info("Batch processing disabled, using original message bus")
            return

        # Create batcher
        self._batcher = MessageBatcher(
            config=self._batch_config,
            batch_processor=self._process_batch,
        )

        await self._batcher.start()

        # Wrap the publish method
        self._message_bus.publish = self._publish_batched

        logger.info("BatchMessageBus started")

    async def stop(self) -> None:
        """Stop batch processing"""
        if self._batcher:
            await self._batcher.stop()

            # Restore original publish method
            self._message_bus.publish = self._original_publish

        logger.info("BatchMessageBus stopped")

    async def _publish_batched(self, message: AgentMessage) -> bool:
        """
        Publish a message using batch processing

        Args:
            message: Message to publish

        Returns:
            True if message was queued
        """
        if self._batcher:
            return await self._batcher.enqueue(message)
        else:
            # Fallback to original
            return await self._original_publish(message)

    async def _process_batch(self, batch: List[AgentMessage]) -> None:
        """
        Process a batch of messages through the original message bus

        Args:
            batch: List of messages to process
        """
        # Process each message through the original bus
        # Note: We still call the original publish for each message,
        # but we do it in a batch to reduce lock contention
        for message in batch:
            await self._original_publish(message)

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        if self._batcher:
            return {
                "batch_processing": self._batcher.get_stats(),
                "queue_size": self._batcher.get_queue_size(),
            }
        return {}

    def get_config(self) -> Dict[str, Any]:
        """Get batch configuration"""
        return {
            "enabled": self._batch_config.enabled,
            "max_batch_size": self._batch_config.max_batch_size,
            "max_wait_time": self._batch_config.max_wait_time,
            "immediate_types": list(self._batch_config.immediate_types),
            "max_queue_size": self._batch_config.max_queue_size,
        }


def create_batch_message_bus(
    message_bus: Any,
    max_batch_size: int = 100,
    max_wait_time: float = 0.1,
    enabled: bool = True,
) -> BatchMessageBus:
    """
    Create a batch message bus wrapper

    Args:
        message_bus: AgentMessageBus instance
        max_batch_size: Maximum batch size
        max_wait_time: Maximum wait time in seconds
        enabled: Whether to enable batch processing

    Returns:
        BatchMessageBus instance
    """
    config = BatchConfig(
        max_batch_size=max_batch_size,
        max_wait_time=max_wait_time,
        enabled=enabled,
    )

    return BatchMessageBus(message_bus, config)
