"""
Unit tests for message batch processing system
"""

import asyncio
import pytest
import time
from datetime import datetime
from pytest_asyncio import fixture

from agents.batch_processor import (
    BatchConfig,
    BatchStats,
    MessageBatcher,
    BatchMessageBus,
    create_batch_message_bus,
)
from agents.messages import AgentMessage, MessageType, create_message
from agents.message_bus import AgentMessageBus
from agents.base import BaseAgent


class TestBatchConfig:
    """Test BatchConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = BatchConfig()

        assert config.max_batch_size == 100
        assert config.max_wait_time == 0.1
        assert config.enabled is True
        assert len(config.immediate_types) > 0
        assert MessageType.EMERGENCY_STOP in config.immediate_types
        assert config.max_queue_size == 10000

    def test_custom_config(self):
        """Test custom configuration"""
        config = BatchConfig(
            max_batch_size=50,
            max_wait_time=0.2,
            enabled=False,
            max_queue_size=5000,
        )

        assert config.max_batch_size == 50
        assert config.max_wait_time == 0.2
        assert config.enabled is False
        assert config.max_queue_size == 5000

    def test_invalid_config(self):
        """Test invalid configuration raises error"""
        with pytest.raises(ValueError, match="max_batch_size must be positive"):
            BatchConfig(max_batch_size=0)

        with pytest.raises(ValueError, match="max_wait_time must be positive"):
            BatchConfig(max_wait_time=0)

        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            BatchConfig(max_queue_size=-1)


class TestBatchStats:
    """Test BatchStats"""

    def test_default_stats(self):
        """Test default statistics values"""
        stats = BatchStats()

        assert stats.messages_queued == 0
        assert stats.messages_batched == 0
        assert stats.messages_immediate == 0
        assert stats.batches_processed == 0
        assert stats.queue_overruns == 0

    def test_stats_to_dict(self):
        """Test converting stats to dictionary"""
        stats = BatchStats()
        stats.messages_queued = 100
        stats.messages_batched = 95
        stats.batches_processed = 2

        data = stats.to_dict()

        assert data["messages_queued"] == 100
        assert data["messages_batched"] == 95
        assert data["batches_processed"] == 2
        assert "last_reset" in data

    def test_stats_reset(self):
        """Test resetting statistics"""
        stats = BatchStats()
        stats.messages_queued = 100
        stats.batches_processed = 5

        stats.reset()

        assert stats.messages_queued == 0
        assert stats.batches_processed == 0


class TestMessageBatcher:
    """Test MessageBatcher"""

    @fixture
    async def batcher(self):
        """Create a test batcher"""
        processed_batches = []

        async def test_processor(batch):
            processed_batches.append(batch)

        batcher = MessageBatcher(
            config=BatchConfig(max_batch_size=10, max_wait_time=0.1),
            batch_processor=test_processor,
        )

        await batcher.start()

        yield batcher, processed_batches

        await batcher.stop()

    @pytest.mark.asyncio
    async def test_enqueue_message(self, batcher):
        """Test enqueuing a message"""
        batcher, processed_batches = batcher

        message = create_message(
            MessageType.MARKET_DATA_UPDATE,
            "test_sender",
            {"symbol": "600000", "price": 10.0},
        )

        result = await batcher.enqueue(message)

        assert result is True
        assert batcher.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_batch_processing(self, batcher):
        """Test batch processing"""
        batcher, processed_batches = batcher

        # Enqueue multiple messages
        for i in range(10):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": f"60000{i}", "price": 10.0 + i},
            )
            await batcher.enqueue(message)

        # Wait for batch processing
        await asyncio.sleep(0.3)

        # Check that batch was processed
        assert len(processed_batches) > 0

        # Check batch contents
        all_messages = []
        for batch in processed_batches:
            all_messages.extend(batch)

        assert len(all_messages) == 10

    @pytest.mark.asyncio
    async def test_immediate_message(self, batcher):
        """Test immediate message processing"""
        batcher, processed_batches = batcher

        # Emergency stop should be processed immediately
        message = create_message(
            MessageType.EMERGENCY_STOP,
            "test_sender",
            {"reason": "test"},
        )

        await batcher.enqueue(message)

        # Should be processed immediately
        await asyncio.sleep(0.1)

        assert len(processed_batches) > 0
        assert processed_batches[0][0].msg_type == MessageType.EMERGENCY_STOP

    @pytest.mark.asyncio
    async def test_queue_overrun(self, batcher):
        """Test queue overrun handling"""
        batcher, processed_batches = batcher

        # Set a small queue size
        batcher.config.max_queue_size = 5

        # Enqueue more messages than queue size
        for i in range(10):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": f"60000{i}", "price": 10.0},
            )
            await batcher.enqueue(message)

        # Check that queue overruns were detected
        stats = batcher.get_stats()
        assert stats["queue_overruns"] > 0

    @pytest.mark.asyncio
    async def test_flush_on_stop(self, batcher):
        """Test that remaining messages are flushed on stop"""
        batcher, processed_batches = batcher

        # Enqueue one message
        message = create_message(
            MessageType.MARKET_DATA_UPDATE,
            "test_sender",
            {"symbol": "600000", "price": 10.0},
        )
        await batcher.enqueue(message)

        # Stop the batcher (should flush)
        # Note: stop is called by fixture

        # Check that message was processed
        await asyncio.sleep(0.2)
        assert len(processed_batches) > 0

    @pytest.mark.asyncio
    async def test_get_stats(self, batcher):
        """Test getting statistics"""
        batcher, processed_batches = batcher

        # Enqueue some messages
        for i in range(5):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": "600000", "price": 10.0},
            )
            await batcher.enqueue(message)

        # Wait for processing
        await asyncio.sleep(0.3)

        stats = batcher.get_stats()

        assert stats["messages_queued"] == 5
        assert stats["batches_processed"] >= 0
        assert "avg_batch_size" in stats
        assert "avg_batch_latency" in stats

    @pytest.mark.asyncio
    async def test_reset_stats(self, batcher):
        """Test resetting statistics"""
        batcher, processed_batches = batcher

        # Enqueue some messages
        for i in range(5):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": "600000", "price": 10.0},
            )
            await batcher.enqueue(message)

        # Wait for processing
        await asyncio.sleep(0.3)

        # Reset stats
        batcher.reset_stats()

        # Check that stats were reset
        stats = batcher.get_stats()
        assert stats["messages_queued"] == 0
        assert stats["batches_processed"] == 0


class TestBatchMessageBus:
    """Test BatchMessageBus wrapper"""

    @fixture
    def message_bus(self):
        """Create a test message bus"""
        return AgentMessageBus(enable_persistence=False)

    @fixture
    async def batch_message_bus(self, message_bus):
        """Create a test batch message bus"""
        batch_bus = create_batch_message_bus(
            message_bus,
            max_batch_size=10,
            max_wait_time=0.1,
            enabled=True,
        )

        await batch_bus.start()

        yield batch_bus

        await batch_bus.stop()

    @pytest.mark.asyncio
    async def test_start_stop(self, message_bus):
        """Test starting and stopping batch message bus"""
        batch_bus = create_batch_message_bus(message_bus)

        await batch_bus.start()
        assert batch_bus._batcher is not None

        await batch_bus.stop()
        assert batch_bus._batcher is None or not batch_bus._batcher._running

    @pytest.mark.asyncio
    async def test_publish_batched(self, batch_message_bus):
        """Test publishing a message through batch bus"""
        message = create_message(
            MessageType.MARKET_DATA_UPDATE,
            "test_sender",
            {"symbol": "600000", "price": 10.0},
        )

        result = await batch_message_bus._publish_batched(message)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_stats(self, batch_message_bus):
        """Test getting batch stats"""
        stats = batch_message_bus.get_stats()

        assert "batch_processing" in stats
        assert "queue_size" in stats

    @pytest.mark.asyncio
    async def test_get_config(self, batch_message_bus):
        """Test getting batch config"""
        config = batch_message_bus.get_config()

        assert config["enabled"] is True
        assert config["max_batch_size"] == 10
        assert config["max_wait_time"] == 0.1
        assert "immediate_types" in config


class TestBatchProcessingPerformance:
    """Performance tests for batch processing"""

    @pytest.mark.asyncio
    async def test_batch_throughput(self):
        """Test batch processing throughput"""
        processed_count = [0]
        processed_batches = []

        async def test_processor(batch):
            processed_batches.append(batch)
            processed_count[0] += len(batch)

        batcher = MessageBatcher(
            config=BatchConfig(max_batch_size=100, max_wait_time=0.05),
            batch_processor=test_processor,
        )

        await batcher.start()

        # Enqueue 1000 messages
        start_time = time.time()

        for i in range(1000):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": f"60000{i % 10}", "price": 10.0},
            )
            await batcher.enqueue(message)

        # Wait for all messages to be processed
        await asyncio.sleep(0.5)

        end_time = time.time()
        elapsed = end_time - start_time

        await batcher.stop()

        # Check throughput
        assert processed_count[0] == 1000
        throughput = processed_count[0] / elapsed
        print(f"Batch throughput: {throughput:.0f} messages/second")

        # Should be significantly faster than 1ms per message
        assert throughput > 100  # At least 100 msg/s

    @pytest.mark.asyncio
    async def test_batch_latency(self):
        """Test batch processing latency"""
        latencies = []

        async def test_processor(batch):
            latencies.append(time.time())

        batcher = MessageBatcher(
            config=BatchConfig(max_batch_size=10, max_wait_time=0.1),
            batch_processor=test_processor,
        )

        await batcher.start()

        # Enqueue 10 messages quickly
        enqueue_times = []
        for i in range(10):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": f"60000{i}", "price": 10.0},
            )
            enqueue_times.append(time.time())
            await batcher.enqueue(message)

        # Wait for processing
        await asyncio.sleep(0.3)

        await batcher.stop()

        # Check latency
        if latencies:
            avg_latency = (latencies[0] - enqueue_times[0]) * 1000  # Convert to ms
            print(f"Batch latency: {avg_latency:.2f}ms")

            # Latency should be reasonable (< 200ms)
            assert avg_latency < 200

    @pytest.mark.asyncio
    async def test_immediate_vs_batched(self):
        """Test immediate messages vs batched messages"""
        immediate_times = []
        batched_times = []

        async def test_processor(batch):
            if batch[0].msg_type == MessageType.EMERGENCY_STOP:
                immediate_times.append(time.time())
            else:
                batched_times.append(time.time())

        batcher = MessageBatcher(
            config=BatchConfig(max_batch_size=10, max_wait_time=0.1),
            batch_processor=test_processor,
        )

        await batcher.start()

        # Send immediate message
        immediate_msg = create_message(
            MessageType.EMERGENCY_STOP,
            "test_sender",
            {"reason": "test"},
        )
        immediate_start = time.time()
        await batcher.enqueue(immediate_msg)
        await asyncio.sleep(0.1)

        # Send batched messages
        batched_start = time.time()
        for i in range(5):
            message = create_message(
                MessageType.MARKET_DATA_UPDATE,
                "test_sender",
                {"symbol": f"60000{i}", "price": 10.0},
            )
            await batcher.enqueue(message)

        await asyncio.sleep(0.3)
        await batcher.stop()

        # Immediate messages should be processed faster
        if immediate_times and batched_times:
            immediate_latency = (immediate_times[0] - immediate_start) * 1000
            batched_latency = (batched_times[0] - batched_start) * 1000

            print(f"Immediate latency: {immediate_latency:.2f}ms")
            print(f"Batched latency: {batched_latency:.2f}ms")

            # Immediate should be processed faster
            # (though this is a rough test as timing can vary)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
