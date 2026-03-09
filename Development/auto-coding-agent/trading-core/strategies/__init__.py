"""
策略引擎框架
Strategy Engine Framework
"""

from .base import (
    BaseStrategy,
    StrategyConfig,
    Signal,
    SignalType,
    StrategyStatus,
    StrategyResult,
    SimpleSignalGenerator,
)
from .engine import (
    StrategyEngine,
    StrategyLoader,
    engine,
    loader,
)
from .ma_strategy import MAStrategy, create_ma_strategy
from .macd_strategy import MACDStrategy, create_macd_strategy
from .kdj_strategy import KDJStrategy, create_kdj_strategy
from .breakout_strategy import BreakoutStrategy, create_breakout_strategy
from .grid_strategy import GridTradingStrategy, create_grid_strategy, GridState

__all__ = [
    # Base
    'BaseStrategy',
    'StrategyConfig',
    'Signal',
    'SignalType',
    'StrategyStatus',
    'StrategyResult',
    'SimpleSignalGenerator',
    # Engine
    'StrategyEngine',
    'StrategyLoader',
    'engine',
    'loader',
    # Strategies
    'MAStrategy',
    'create_ma_strategy',
    'MACDStrategy',
    'create_macd_strategy',
    'KDJStrategy',
    'create_kdj_strategy',
    'BreakoutStrategy',
    'create_breakout_strategy',
    'GridTradingStrategy',
    'create_grid_strategy',
    'GridState',
]
