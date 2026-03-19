# Async Scheduler Tuning Guide

## Overview

The Async Task Scheduler provides priority-based task scheduling with concurrency control for the Trading System. This guide helps you configure and tune the scheduler for optimal performance.

---

## Core Concepts

### Task Priority Levels

Tasks are scheduled based on priority (lower value = higher priority):

| Priority | Value | Use Case | Examples |
|----------|-------|----------|----------|
| CRITICAL | 0 | Emergency operations | Emergency stop, critical errors |
| HIGH | 1 | Time-sensitive operations | Market data updates, trade execution |
| NORMAL | 2 | Regular operations | Strategy calculations, logging |
| LOW | 3 | Background tasks | Data archival, report generation |
| IDLE | 4 | Maintenance tasks | Database cleanup, optimization |

### Concurrency Control

The scheduler uses two-level concurrency control:

1. **Global Concurrency**: Max concurrent tasks across all agents
   - Configured via `max_concurrent_tasks`
   - Default: 100 tasks

2. **Per-Agent Concurrency**: Max concurrent messages per agent
   - Configured via `max_concurrent_per_agent` in AgentConcurrencyManager
   - Default: 10 messages per agent

---

## Configuration Parameters

### Scheduler Configuration

```python
from agents.async_scheduler import ConcurrencyConfig

config = ConcurrencyConfig(
    max_concurrent_tasks=100,      # Maximum concurrent tasks
    max_queue_size=1000,           # Maximum queued tasks
    task_timeout=30.0,             # Default task timeout (seconds)
    queue_timeout=5.0,             # Queue wait timeout
    enable_priorities=True,        # Enable priority scheduling
    enable_monitoring=True,        # Enable performance monitoring
)
```

### Parameter Tuning Guidelines

#### max_concurrent_tasks

**Recommended values:**
- Low load (10 agents): 50
- Medium load (10-50 agents): 100
- High load (50+ agents): 200-500

**Tuning approach:**
1. Start with `CPU count * 10`
2. Monitor CPU utilization
3. Increase if CPU < 70%
4. Decrease if CPU > 90%

#### max_queue_size

**Recommended values:**
- Small systems: 500
- Medium systems: 1000
- Large systems: 5000+

**Considerations:**
- Larger queues = more memory usage
- Too small = tasks rejected
- Too large = delayed processing

#### task_timeout

**Recommended values:**
- Fast operations (API calls): 5-10 seconds
- Medium operations (calculations): 30-60 seconds
- Slow operations (data processing): 300+ seconds

**Formula:**
```
task_timeout = p95_operation_time * 1.5
```

#### queue_timeout

**Recommended values:**
- Real-time systems: 1-2 seconds
- Normal systems: 5-10 seconds
- Batch systems: 30+ seconds

---

## Performance Tuning

### 1. Identify Bottlenecks

Check scheduler statistics:

```bash
curl http://localhost:8000/api/async-scheduler/stats
```

Key metrics:
- `avg_wait_time`: Time tasks spend in queue
- `avg_run_time`: Time tasks take to execute
- `success_rate`: Percentage of successful tasks
- `queue_utilization`: Current queue usage

### 2. Tune for Throughput

**Goal**: Maximize tasks per second

```
Throughput = tasks_completed / total_time
```

**Tuning:**
- Increase `max_concurrent_tasks` until CPU ~80%
- Increase `max_queue_size` to prevent rejections
- Reduce `task_timeout` to free up slots faster

**Target:** >100 tasks/second for typical workloads

### 3. Tune for Latency

**Goal**: Minimize wait time for critical tasks

**Tuning:**
- Use CRITICAL/HIGH priority for time-sensitive tasks
- Reduce `max_concurrent_tasks` to lower queue wait
- Enable priority-based scheduling (`enable_priorities=True`)

**Target:**
- CRITICAL: <10ms wait
- HIGH: <50ms wait
- NORMAL: <200ms wait

### 4. Tune for Reliability

**Goal**: Minimize failures and timeouts

**Tuning:**
- Increase `task_timeout` to 2x p95 execution time
- Monitor `failure_rate` and `timeout_rate`
- Implement retry logic for failed tasks
- Use proper error handling in tasks

**Target:**
- Success rate: >99%
- Timeout rate: <1%
- Failure rate: <0.1%

---

## Common Scenarios

### Scenario 1: High Market Data Volume

**Symptoms:**
- High queue utilization (>80%)
- Increasing wait times
- Dropped messages

**Solution:**
```python
config = ConcurrencyConfig(
    max_concurrent_tasks=200,      # Increase concurrency
    max_queue_size=5000,           # Larger queue
    task_timeout=10.0,             # Shorter timeout
    enable_priorities=True,        # Prioritize market data
)
```

### Scenario 2: Slow Strategy Calculations

**Symptoms:**
- High task timeout rate
- Tasks backing up in queue

**Solution:**
```python
# Use higher priority for time-sensitive strategies
await scheduler.submit(
    calculate_signals,
    priority=TaskPriority.HIGH,
    timeout=60.0,  # Longer timeout for slow tasks
)
```

### Scenario 3: Memory Pressure

**Symptoms:**
- High memory usage
- System slowdowns

**Solution:**
```python
config = ConcurrencyConfig(
    max_concurrent_tasks=50,       # Reduce concurrency
    max_queue_size=500,            # Smaller queue
    task_timeout=30.0,
)
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/async-scheduler/health
```

**Health indicators:**
- `status`: healthy, degraded, or unhealthy
- `queue_utilization`: <80% is healthy
- `failure_rate`: <1% is healthy
- `avg_wait_time`: <1s is healthy

### Performance Monitoring

```bash
# Get scheduler statistics
curl http://localhost:8000/api/async-scheduler/stats

# Get concurrency info
curl http://localhost:8000/api/async-scheduler/concurrency
```

### Alerts

Set up alerts for:
- Queue utilization > 80%
- Failure rate > 1%
- Timeout rate > 0.5%
- Average wait time > 1s

---

## Best Practices

### 1. Use Appropriate Priorities

```python
# ✅ Good - time-sensitive market data
await scheduler.submit(
    process_market_data,
    priority=TaskPriority.HIGH,
)

# ✅ Good - background maintenance
await scheduler.submit(
    cleanup_old_data,
    priority=TaskPriority.IDLE,
)

# ❌ Bad - everything at NORMAL priority
await scheduler.submit(
    emergency_stop,
    priority=TaskPriority.NORMAL,  # Should be CRITICAL!
)
```

### 2. Set Reasonable Timeouts

```python
# ✅ Good - timeout based on expected execution time
await scheduler.submit(
    calculate_signals,
    timeout=30.0,  # Expected to complete in 10-20s
)

# ❌ Bad - too short
await scheduler.submit(
    calculate_signals,
    timeout=0.1,  # Will timeout!
)

# ❌ Bad - too long
await scheduler.submit(
    quick_check,
    timeout=300.0,  # Wastes resources if stuck
)
```

### 3. Handle Errors Gracefully

```python
async def robust_task():
    try:
        result = await some_operation()
        return result
    except asyncio.TimeoutError:
        logger.error("Task timed out")
        return None
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise

await scheduler.submit(robust_task)
```

### 4. Monitor Task Completion

```python
async def task_with_callback(result):
    logger.info(f"Task completed: {result}")

await scheduler.submit(
    some_task,
    callback=task_with_callback,
)
```

---

## API Examples

### Submit a Task

```bash
curl -X POST "http://localhost:8000/api/async-scheduler/tasks/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "my_task",
    "priority": "HIGH",
    "timeout": 30.0,
    "metadata": {"symbol": "600000"}
  }'
```

### Get Task Info

```bash
curl http://localhost:8000/api/async-scheduler/tasks/my_task
```

### Cancel a Task

```bash
curl -X DELETE http://localhost:8000/api/async-scheduler/tasks/my_task
```

### Update Configuration

```bash
curl -X POST "http://localhost:8000/api/async-scheduler/config" \
  -H "Content-Type: application/json" \
  -d '{
    "max_concurrent_tasks": 200,
    "max_queue_size": 5000
  }'
```

---

## Troubleshooting

### Problem: Tasks Timing Out

**Diagnosis:**
```bash
curl http://localhost:8000/api/async-scheduler/stats | jq '.tasks_timeout'
```

**Solutions:**
1. Increase `task_timeout`
2. Optimize slow tasks
3. Break long tasks into smaller chunks

### Problem: Queue Full Errors

**Diagnosis:**
```bash
curl http://localhost:8000/api/async-scheduler/health | jq '.metrics.queue_utilization'
```

**Solutions:**
1. Increase `max_queue_size`
2. Increase `max_concurrent_tasks`
3. Reduce task submission rate
4. Use task priorities more effectively

### Problem: High Failure Rate

**Diagnosis:**
```bash
curl http://localhost:8000/api/async-scheduler/stats | jq '.failure_rate'
```

**Solutions:**
1. Check task error handling
2. Review system resources (CPU, memory)
3. Reduce concurrency
4. Fix problematic tasks

---

## Advanced Topics

### Custom Task Prioritization

```python
# Dynamic priority based on market conditions
async def submit_market_task(symbol, is_fast_moving):
    priority = TaskPriority.CRITICAL if is_fast_moving else TaskPriority.HIGH
    await scheduler.submit(
        process_market_data,
        priority=priority,
        metadata={"symbol": symbol, "fast_moving": is_fast_moving},
    )
```

### Task Chaining

```python
async def task_chain():
    # Run tasks sequentially
    result1 = await task1()
    result2 = await task2(result1)
    return await task3(result2)

await scheduler.submit(task_chain)
```

### Task Batching

```python
async def batch_task(items):
    # Process multiple items in one task
    results = []
    for item in items:
        result = await process_item(item)
        results.append(result)
    return results

# More efficient than many small tasks
await scheduler.submit(batch_task, items=[...])
```

---

## Summary

**Key Takeaways:**
1. Start with default configuration
2. Monitor metrics continuously
3. Tune based on workload characteristics
4. Use priorities appropriately
5. Set reasonable timeouts
6. Handle errors gracefully
7. Test under load before production

**Quick Reference:**
- API: `http://localhost:8000/api/async-scheduler/*`
- Health: `/api/async-scheduler/health`
- Stats: `/api/async-scheduler/stats`
- Config: `/api/async-scheduler/config`

For more information, see the main documentation or API reference.
