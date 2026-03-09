"""
Pytest configuration and shared fixtures.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    import random

    data = {
        "open": [10.0 + i * 0.1 + random.uniform(-0.5, 0.5) for i in range(100)],
        "high": [10.2 + i * 0.1 + random.uniform(-0.3, 0.5) for i in range(100)],
        "low": [9.8 + i * 0.1 + random.uniform(-0.5, 0.3) for i in range(100)],
        "close": [10.0 + i * 0.1 + random.uniform(-0.3, 0.3) for i in range(100)],
        "volume": [100000 + random.randint(-10000, 10000) for i in range(100)],
    }
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def sample_market_data():
    """Sample real-time market quote data."""
    return {
        "symbol": "600000",
        "name": "浦发银行",
        "price": 10.50,
        "change": 0.25,
        "change_percent": 2.44,
        "volume": 1500000,
        "amount": 15750000,
        "bid": 10.49,
        "ask": 10.50,
        "high": 10.65,
        "low": 10.30,
        "open": 10.35,
        "prev_close": 10.25,
    }


@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration."""
    from strategies.base import StrategyConfig

    return StrategyConfig(
        id="test_strategy",
        name="Test Strategy",
        symbols=["600000", "000001"],
        parameters={"short_period": 5, "long_period": 20},
        risk_parameters={
            "max_position_size": 10000,
            "max_position_percent": 0.2,
            "stop_loss_percent": 0.05,
        },
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()

    # Mock table method
    def mock_table(table_name):
        table = Mock()
        table.select = Mock(return_value=table)
        table.insert = Mock(return_value=table)
        table.update = Mock(return_value=table)
        table.delete = Mock(return_value=table)
        table.eq = Mock(return_value=table)
        table.order = Mock(return_value=table)
        table.limit = Mock(return_value=table)
        table.execute = Mock(return_value=Mock(data=[], count=0))
        return table

    client.table = mock_table
    client.auth = Mock()
    client.auth.get_user = Mock(return_value=Mock(data=Mock(user=Mock(id="test_user"))))

    return client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client for API testing."""
    client = AsyncMock()

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json = AsyncMock(return_value={"data": {"code": 0, "data": {}}})
        response.text = ""
        return response

    client.get = mock_get
    return client


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test_user_12345"


@pytest.fixture
def sample_order():
    """Sample order data."""
    return {
        "id": "order_001",
        "user_id": "test_user_12345",
        "symbol": "600000",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": 1000,
        "price": 10.50,
        "status": "pending",
        "filled_quantity": 0,
        "avg_price": 0.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_position():
    """Sample position data."""
    return {
        "id": "pos_001",
        "user_id": "test_user_12345",
        "symbol": "600000",
        "quantity": 1000,
        "cost_price": 10.20,
        "current_price": 10.50,
        "market_value": 10500,
        "profit_loss": 300,
        "profit_loss_percent": 2.94,
    }


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
