"""
Performance Testing API

Provides endpoints for running and managing performance tests.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from testing.performance.stress_test import (
    StressTestSuite,
    run_quick_stress_test,
    run_full_stress_test,
)


router = APIRouter(
    prefix="/api/performance-testing",
    tags=["performance-testing"],
)


class StressTestConfig(BaseModel):
    """Stress test configuration"""
    test_type: str = "quick"  # quick or full
    requests_per_second: Optional[float] = None
    duration: Optional[float] = None


@router.post("/run")
async def run_stress_test(
    config: StressTestConfig,
    background_tasks: BackgroundTasks,
):
    """
    Run a stress test

    Args:
        config: Test configuration

    Returns:
        Test execution info
    """
    if config.test_type == "full":
        # Run in background
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(_run_full_test_background(test_id))

        return {
            "test_id": test_id,
            "status": "running",
            "message": "Full stress test started in background",
            "timestamp": datetime.now().isoformat(),
        }
    else:
        # Quick test (synchronous)
        logger.info("Running quick stress test...")
        result = await run_quick_stress_test()

        return {
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/results")
async def get_test_results(
    limit: int = Query(10, description="Maximum results to return"),
):
    """
    Get recent test results

    Args:
        limit: Maximum results

    Returns:
        List of test results
    """
    from pathlib import Path

    results_dir = Path("data/performance_tests")
    if not results_dir.exists():
        return {
            "results": [],
            "count": 0,
            "timestamp": datetime.now().isoformat(),
        }

    # Get recent summary files
    summary_files = sorted(
        results_dir.glob("stress_test_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]

    results = []
    for file in summary_files:
        try:
            import json
            with open(file, "r") as f:
                data = json.load(f)
                results.append({
                    "file": file.name,
                    "data": data,
                })
        except Exception as e:
            logger.warning(f"Could not read {file}: {e}")

    return {
        "results": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/results/{test_id}")
async def get_test_result(test_id: str):
    """
    Get specific test result

    Args:
        test_id: Test ID

    Returns:
        Test result details
    """
    from pathlib import Path

    results_dir = Path("data/performance_tests")
    summary_file = results_dir / f"stress_test_summary_{test_id}.json"

    if not summary_file.exists():
        raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")

    import json
    with open(summary_file, "r") as f:
        data = json.load(f)

    return {
        "test_id": test_id,
        "result": data,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/latest")
async def get_latest_results():
    """
    Get latest test results

    Returns:
        Most recent test results
    """
    from pathlib import Path

    results_dir = Path("data/performance_tests")

    if not results_dir.exists():
        raise HTTPException(status_code=404, detail="No test results found")

    # Get most recent summary
    summary_files = sorted(
        results_dir.glob("stress_test_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not summary_files:
        raise HTTPException(status_code=404, detail="No test results found")

    # Get latest
    import json
    with open(summary_files[0], "r") as f:
        summary_data = json.load(f)

    # Try to get detailed results too
    detail_file = summary_files[0].name.replace("summary_", "results_")
    detail_path = results_dir / detail_file

    detailed_results = None
    if detail_path.exists():
        with open(detail_path, "r") as f:
            detailed_results = json.load(f)

    return {
        "summary": summary_data,
        "detailed_results": detailed_results,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
async def get_testing_status():
    """
    Get testing system status

    Returns:
        Testing status and info
    """
    from pathlib import Path

    results_dir = Path("data/performance_tests")

    if not results_dir.exists():
        return {
            "has_results": False,
            "result_count": 0,
            "latest_test": None,
            "timestamp": datetime.now().isoformat(),
        }

    summary_files = list(results_dir.glob("stress_test_summary_*.json"))

    latest_test = None
    if summary_files:
        latest_file = max(summary_files, key=lambda p: p.stat().st_mtime)
        import json
        try:
            with open(latest_file, "r") as f:
                latest_test = json.load(f)
        except Exception:
            pass

    return {
        "has_results": True,
        "result_count": len(summary_files),
        "latest_test": latest_test,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/benchmarks")
async def get_benchmarks():
    """
    Get performance benchmarks and thresholds

    Returns:
        Benchmark thresholds
    """
    return {
        "benchmarks": {
            "message_throughput": {
                "target": 1000,  # messages per second
                "acceptable": 500,
                "critical": 100,
            },
            "avg_latency": {
                "target": 10,  # milliseconds
                "acceptable": 50,
                "critical": 100,
            },
            "p95_latency": {
                "target": 20,  # milliseconds
                "acceptable": 100,
                "critical": 200,
            },
            "cpu_usage": {
                "target": 50,  # percent
                "acceptable": 80,
                "critical": 95,
            },
            "memory_leak": {
                "target": 0,  # MB per minute
                "acceptable": 1,
                "critical": 10,
            },
            "error_rate": {
                "target": 0.01,  # 1%
                "acceptable": 0.05,
                "critical": 0.1,
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


async def _run_full_test_background(test_id: str) -> None:
    """Run full test in background"""
    try:
        logger.info(f"Starting full stress test: {test_id}")
        result = await run_full_stress_test()
        logger.info(f"Full stress test complete: {test_id}")
    except Exception as e:
        logger.error(f"Full stress test failed: {e}")
