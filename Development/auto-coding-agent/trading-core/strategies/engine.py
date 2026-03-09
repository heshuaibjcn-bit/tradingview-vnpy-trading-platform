"""
策略执行引擎
Strategy Execution Engine

Manages strategy lifecycle, signal generation, and execution
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, time
from pathlib import Path
import json

from .base import (
    BaseStrategy,
    StrategyConfig,
    Signal,
    SignalType,
    StrategyStatus,
    StrategyResult,
)
from market.fetcher import RealtimeQuote, get_realtime_quote
from utils.logger import logger


class StrategyEngine:
    """
    Strategy execution engine

    Manages multiple strategies, coordinates their execution,
    and handles signal dispatching
    """

    def __init__(self):
        """Initialize strategy engine"""
        self._strategies: Dict[str, BaseStrategy] = {}
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._signal_listeners: List[Callable[[Signal], None]] = []

        # Risk limits
        self.max_signals_per_minute = 10
        self._signal_count = 0
        self._signal_window_start: Optional[datetime] = None

        logger.info("StrategyEngine initialized")

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """
        Add strategy to engine

        Args:
            strategy: Strategy instance
        """
        self._strategies[strategy.name] = strategy
        logger.info(f"Strategy added: {strategy.name}")

    def remove_strategy(self, name: str) -> bool:
        """
        Remove strategy from engine

        Args:
            name: Strategy name

        Returns:
            True if removed, False if not found
        """
        if name in self._strategies:
            del self._strategies[name]
            logger.info(f"Strategy removed: {name}")
            return True
        return False

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """
        Get strategy by name

        Args:
            name: Strategy name

        Returns:
            Strategy or None
        """
        return self._strategies.get(name)

    def list_strategies(self) -> List[str]:
        """Get list of strategy names"""
        return list(self._strategies.keys())

    def get_enabled_strategies(self) -> List[BaseStrategy]:
        """Get list of enabled strategies"""
        return [
            s for s in self._strategies.values()
            if s.is_enabled
        ]

    async def execute_strategy(self, name: str) -> StrategyResult:
        """
        Execute single strategy

        Args:
            name: Strategy name

        Returns:
            Strategy execution result
        """
        strategy = self.get_strategy(name)

        if not strategy:
            return StrategyResult(
                success=False,
                status=StrategyStatus.ERROR,
                message=f"Strategy not found: {name}"
            )

        if not strategy.is_enabled:
            return StrategyResult(
                success=False,
                status=StrategyStatus.IDLE,
                message=f"Strategy not enabled: {name}"
            )

        logger.info(f"Executing strategy: {name}")
        return await strategy.execute()

    async def execute_all_strategies(self) -> Dict[str, StrategyResult]:
        """
        Execute all enabled strategies

        Returns:
            Dictionary mapping strategy name to result
        """
        logger.info("Executing all enabled strategies")

        enabled = self.get_enabled_strategies()
        results = {}

        for strategy in enabled:
            try:
                result = await strategy.execute()
                results[strategy.name] = result

            except Exception as e:
                logger.error(f"Error executing strategy {strategy.name}: {e}")
                results[strategy.name] = StrategyResult(
                    success=False,
                    status=StrategyStatus.ERROR,
                    message=str(e)
                )

        return results

    def add_signal_listener(self, listener: Callable[[Signal], None]) -> None:
        """
        Add signal listener

        Args:
            listener: Function to call when signal is generated
        """
        self._signal_listeners.append(listener)
        logger.debug("Signal listener added")

    async def _dispatch_signal(self, signal: Signal) -> None:
        """Dispatch signal to all listeners"""
        for listener in self._signal_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(signal)
                else:
                    listener(signal)
            except Exception as e:
                logger.error(f"Error in signal listener: {e}")

    async def start(self, interval: float = 5.0) -> None:
        """
        Start strategy engine

        Args:
            interval: Execution interval in seconds
        """
        if self._is_running:
            logger.warning("Strategy engine already running")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop(interval))

        logger.info(f"Strategy engine started (interval: {interval}s)")

    async def stop(self) -> None:
        """Stop strategy engine"""
        if not self._is_running:
            logger.warning("Strategy engine not running")
            return

        self._is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Strategy engine stopped")

    async def _run_loop(self, interval: float) -> None:
        """Main execution loop"""
        logger.info("Strategy engine loop started")

        while self._is_running:
            try:
                # Reset signal count if window expired
                now = datetime.now()
                if (self._signal_window_start and
                    now - self._signal_window_start >= timedelta(minutes=1)):
                    self._signal_count = 0
                    self._signal_window_start = None

                # Execute all enabled strategies
                results = await self.execute_all_strategies()

                # Process signals
                for result in results.values():
                    if result.success:
                        for signal in result.signals:
                            await self._dispatch_signal(signal)

                            # Update signal count
                            self._signal_count += 1
                            if self._signal_window_start is None:
                                self._signal_window_start = now

                            # Check rate limit
                            if self._signal_count >= self.max_signals_per_minute:
                                logger.warning(
                                    f"Signal rate limit reached: {self._signal_count}/min"
                                )
                                # Wait until window expires
                                sleep_time = 60 - (now - self._signal_window_start).seconds
                                await asyncio.sleep(sleep_time)
                                self._signal_count = 0
                                self._signal_window_start = None

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Strategy engine loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in strategy engine loop: {e}")
                await asyncio.sleep(interval)

        logger.info("Strategy engine loop stopped")


class StrategyLoader:
    """
    Strategy configuration loader
    """

    def __init__(self, config_dir: str = "config/strategies"):
        """
        Initialize strategy loader

        Args:
            config_dir: Directory containing strategy configs
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, config: StrategyConfig) -> Path:
        """
        Save strategy configuration to file

        Args:
            config: Strategy configuration

        Returns:
            Path to saved config file
        """
        filename = f"{config.name}.json"
        filepath = self.config_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(config.model_dump_json(indent=2, ensure_ascii=False))

        logger.info(f"Strategy config saved: {filepath}")
        return filepath

    def load_config(self, name: str) -> Optional[StrategyConfig]:
        """
        Load strategy configuration from file

        Args:
            name: Strategy name

        Returns:
            Strategy configuration or None if not found
        """
        filename = f"{name}.json"
        filepath = self.config_dir / filename

        if not filepath.exists():
            logger.warning(f"Strategy config not found: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        config = StrategyConfig(**data)
        logger.info(f"Strategy config loaded: {name}")
        return config

    def list_configs(self) -> List[str]:
        """Get list of available strategy configs"""
        configs = []

        for filepath in self.config_dir.glob("*.json"):
            configs.append(filepath.stem)

        return sorted(configs)

    def delete_config(self, name: str) -> bool:
        """
        Delete strategy configuration

        Args:
            name: Strategy name

        Returns:
            True if deleted, False if not found
        """
        filename = f"{name}.json"
        filepath = self.config_dir / filename

        if filepath.exists():
            filepath.unlink()
            logger.info(f"Strategy config deleted: {name}")
            return True

        return False


# Global strategy engine instance
engine = StrategyEngine()
loader = StrategyLoader()
