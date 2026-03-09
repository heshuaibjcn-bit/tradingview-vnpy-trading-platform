"""
策略引擎框架
Strategy Engine Framework

Provides base classes and interfaces for trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import asyncio

from market.fetcher import RealtimeQuote, OHLCV
from utils.logger import logger


class SignalType(Enum):
    """Trading signal type"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal(BaseModel):
    """
    Trading signal
    """
    symbol: str
    signal_type: SignalType
    price: float
    quantity: int
    confidence: float = Field(default=1.0, ge=0, le=1)
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            SignalType: lambda v: v.value
        }


class StrategyConfig(BaseModel):
    """
    Strategy configuration
    """
    name: str
    type: str
    enabled: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
    symbols: List[str] = Field(default_factory=list)
    risk_params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyStatus(Enum):
    """Strategy status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class StrategyResult(BaseModel):
    """
    Strategy execution result
    """
    success: bool
    status: StrategyStatus
    signals: List[Signal] = Field(default_factory=list)
    message: str = ""
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            StrategyStatus: lambda v: v.value
        }


class BaseStrategy(ABC):
    """
    Base strategy class

    All trading strategies should inherit from this class
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy

        Args:
            config: Strategy configuration
        """
        self.config = config
        self.status = StrategyStatus.IDLE
        self._signals: List[Signal] = []
        self._callbacks: List[Callable[[Signal], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []

        logger.info(f"Strategy '{config.name}' initialized (type: {config.type})")

    @property
    def name(self) -> str:
        """Get strategy name"""
        return self.config.name

    @property
    def is_enabled(self) -> bool:
        """Check if strategy is enabled"""
        return self.config.enabled

    @property
    def is_running(self) -> bool:
        """Check if strategy is running"""
        return self.status == StrategyStatus.RUNNING

    @abstractmethod
    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """
        Generate trading signal from market data

        Args:
            quote: Realtime market quote

        Returns:
            Signal or None if no signal
        """
        pass

    @abstractmethod
    async def analyze(self, symbol: str) -> List[Signal]:
        """
        Analyze symbol and generate signals

        Args:
            symbol: Stock symbol

        Returns:
            List of signals
        """
        pass

    async def execute(self) -> StrategyResult:
        """
        Execute strategy

        Returns:
            Strategy execution result
        """
        try:
            self.status = StrategyStatus.RUNNING
            logger.info(f"Executing strategy: {self.name}")

            # Generate signals for all symbols
            all_signals = []

            for symbol in self.config.symbols:
                try:
                    # This would fetch real quote in production
                    # For now, we simulate it
                    from market.fetcher import get_realtime_quote

                    quote = await get_realtime_quote(symbol)

                    if quote:
                        signals = await self.analyze(symbol)
                        all_signals.extend(signals)

                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    self._handle_error(e)

            self._signals = all_signals
            self.status = StrategyStatus.IDLE

            result = StrategyResult(
                success=True,
                status=self.status,
                signals=all_signals,
                message=f"Generated {len(all_signals)} signals"
            )

            # Trigger callbacks
            for signal in all_signals:
                await self._notify_callbacks(signal)

            return result

        except Exception as e:
            self.status = StrategyStatus.ERROR
            self._handle_error(e)

            return StrategyResult(
                success=False,
                status=self.status,
                message=f"Strategy execution failed: {str(e)}",
                error=str(e)
            )

    def add_signal_callback(self, callback: Callable[[Signal], None]) -> None:
        """
        Add signal callback

        Args:
            callback: Function to call when signal is generated
        """
        self._callbacks.append(callback)
        logger.debug(f"Added signal callback to strategy {self.name}")

    def add_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """
        Add error callback

        Args:
            callback: Function to call when error occurs
        """
        self._error_callbacks.append(callback)
        logger.debug(f"Added error callback to strategy {self.name}")

    async def _notify_callbacks(self, signal: Signal) -> None:
        """Notify all callbacks of new signal"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(signal)
                else:
                    callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")

    def _handle_error(self, error: Exception) -> None:
        """Handle strategy error"""
        logger.error(f"Strategy {self.name} error: {error}")

        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get strategy parameter"""
        return self.config.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """Set strategy parameter"""
        self.config.parameters[key] = value
        logger.debug(f"Strategy {self.name} parameter updated: {key} = {value}")

    def get_risk_param(self, key: str, default: Any = None) -> Any:
        """Get risk parameter"""
        return self.config.risk_params.get(key, default)

    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif key in self.config.parameters:
                self.config.parameters[key] = value
            elif key in self.config.risk_params:
                self.config.risk_params[key] = value

        logger.info(f"Strategy {self.name} config updated: {kwargs}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, status={self.status.value})>"


class SimpleSignalGenerator(BaseStrategy):
    """
    Simple signal generator strategy for testing

    Generates signals based on simple price thresholds
    """

    async def generate_signal(self, quote: RealtimeQuote) -> Optional[Signal]:
        """Generate signal based on price change"""

        # Get threshold from parameters
        threshold = self.get_parameter("threshold", 0.03)  # 3% default

        if abs(quote.change_percent) >= threshold * 100:
            # Generate signal based on direction
            if quote.change_percent > 0:
                signal_type = SignalType.BUY
            else:
                signal_type = SignalType.SELL

            return Signal(
                symbol=quote.symbol,
                signal_type=signal_type,
                price=quote.price,
                quantity=100,  # Default quantity
                confidence=min(abs(quote.change_percent) / (threshold * 100), 1.0),
                reason=f"Price change {quote.change_percent:.2f}% exceeds threshold {threshold * 100}%"
            )

        return None

    async def analyze(self, symbol: str) -> List[Signal]:
        """Analyze symbol and generate signals"""
        from market.fetcher import get_realtime_quote

        quote = await get_realtime_quote(symbol)

        if quote:
            signal = await self.generate_signal(quote)
            return [signal] if signal else []

        return []
