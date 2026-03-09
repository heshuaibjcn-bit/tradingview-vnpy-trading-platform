"""
Strategy sandbox for simulated trading.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from loguru import logger

from ..strategies.base import BaseStrategy, Signal, StrategyConfig, StrategyResult
from ..logging.recorder import TradeRecorder


class SandboxMode(Enum):
    """Sandbox operation modes."""
    PAPER = "paper"  # Paper trading, no real orders
    SIMULATION = "simulation"  # Historical simulation
    DRY_RUN = "dry_run"  # Generate signals but don't execute
    LIVE = "live"  # Real trading with real orders


@dataclass
class SandboxResult:
    """Result of sandbox strategy execution."""
    strategy_name: str
    mode: SandboxMode
    signals: List[Signal] = field(default_factory=list)
    simulated_trades: List[Dict] = field(default_factory=list)
    profit_loss: float = 0.0
    max_drawdown: float = 0.0
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class StrategySandbox:
    """
    Sandbox for testing strategies without real trading.

    Supports paper trading, simulation, and dry-run modes.
    """

    def __init__(self):
        self._active_sandboxes: Dict[str, "SandboxSession"] = {}
        self._results: List[SandboxResult] = []

    def create_session(
        self,
        session_id: str,
        strategy: BaseStrategy,
        mode: SandboxMode = SandboxMode.PAPER,
        initial_capital: float = 100000.0,
    ) -> "SandboxSession":
        """
        Create a sandbox session for testing a strategy.

        Args:
            session_id: Unique session identifier
            strategy: Strategy to test
            mode: Sandbox mode
            initial_capital: Starting capital for paper trading

        Returns:
            SandboxSession instance
        """
        session = SandboxSession(
            session_id=session_id,
            strategy=strategy,
            mode=mode,
            initial_capital=initial_capital,
        )

        self._active_sandboxes[session_id] = session
        logger.info(
            f"Sandbox session created: {session_id} for strategy {strategy.name}, "
            f"mode: {mode.value}"
        )
        return session

    async def run_session(
        self,
        session_id: str,
        duration_seconds: Optional[int] = None,
        max_signals: int = 10,
    ) -> SandboxResult:
        """
        Run a sandbox session.

        Args:
            session_id: Session identifier
            duration_seconds: How long to run (None = until stopped)
            max_signals: Maximum signals to generate

        Returns:
            SandboxResult
        """
        if session_id not in self._active_sandboxes:
            return SandboxResult(
                strategy_name="unknown",
                mode=SandboxMode.PAPER,
                success=False,
                error=f"Session {session_id} not found"
            )

        session = self._active_sandboxes[session_id]
        return await session.run(duration_seconds, max_signals)

    def stop_session(self, session_id: str) -> Optional[SandboxResult]:
        """Stop a sandbox session and return results."""
        if session_id not in self._active_sandboxes:
            return None

        session = self._active_sandboxes[session_id]
        result = session.stop()
        self._results.append(result)
        del self._active_sandboxes[session_id]

        logger.info(f"Sandbox session stopped: {session_id}")
        return result

    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get status of an active session."""
        if session_id not in self._active_sandboxes:
            return None

        session = self._active_sandboxes[session_id]
        return session.get_status()

    def list_sessions(self) -> List[Dict]:
        """List all active sessions."""
        return [
            {**s.get_status(), "session_id": sid}
            for sid, s in self._active_sandboxes.items()
        ]

    def get_results(self, session_id: Optional[str] = None) -> List[SandboxResult]:
        """Get sandbox results."""
        if session_id:
            return [r for r in self._results if r.strategy_name == session_id]
        return self._results.copy()


class SandboxSession:
    """A single sandbox testing session."""

    def __init__(
        self,
        session_id: str,
        strategy: BaseStrategy,
        mode: SandboxMode,
        initial_capital: float = 100000.0,
    ):
        self.session_id = session_id
        self.strategy = strategy
        self.mode = mode
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.signals_generated: List[Signal] = []
        self.trades_simulated: List[Dict] = []
        self._running = False
        self._stopped = False
        self._start_time: Optional[datetime] = None

    async def run(
        self,
        duration_seconds: Optional[int] = None,
        max_signals: int = 10,
    ) -> SandboxResult:
        """Run the sandbox session."""
        self._running = True
        self._start_time = datetime.now()

        try:
            if self.mode == SandboxMode.PAPER:
                return await self._run_paper_trading(max_signals)
            elif self.mode == SandboxMode.SIMULATION:
                return await self._run_simulation()
            elif self.mode == SandboxMode.DRY_RUN:
                return await self._run_dry_run(max_signals)
            else:
                return SandboxResult(
                    strategy_name=self.strategy.name,
                    mode=self.mode,
                    success=False,
                    error="Live trading not supported in sandbox"
                )

        except Exception as e:
            logger.error(f"Sandbox session error: {e}")
            return SandboxResult(
                strategy_name=self.strategy.name,
                mode=self.mode,
                success=False,
                error=str(e)
            )

    async def _run_paper_trading(self, max_signals: int) -> SandboxResult:
        """Run paper trading simulation."""
        signal_count = 0

        while self._running and not self._stopped and signal_count < max_signals:
            # Generate signals from strategy
            result = await self.strategy.execute()

            for signal in result.signals:
                self.signals_generated.append(signal)

                # Simulate trade execution
                self._simulate_trade(signal)

                signal_count += 1
                if signal_count >= max_signals:
                    break

            # Wait before next check
            await asyncio.sleep(1)

        return self._create_result()

    async def _run_simulation(self) -> SandboxResult:
        """Run historical simulation."""
        # Placeholder for historical simulation
        return SandboxResult(
            strategy_name=self.strategy.name,
            mode=SandboxMode.SIMULATION,
            success=True,
            signals=[],
        )

    async def _run_dry_run(self, max_signals: int) -> SandboxResult:
        """Run dry run (signals only, no simulation)."""
        signal_count = 0

        while self._running and not self._stopped and signal_count < max_signals:
            result = await self.strategy.execute()

            for signal in result.signals:
                self.signals_generated.append(signal)
                signal_count += 1

            await asyncio.sleep(1)

        return self._create_result()

    def _simulate_trade(self, signal: Signal) -> None:
        """Simulate a trade execution."""
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.symbol,
            "side": signal.signal_type.value,
            "price": signal.price,
            "quantity": signal.quantity,
            "signal_reason": signal.reason,
        }

        if signal.signal_type.value == "buy":
            self.positions[signal.symbol] = (
                self.positions.get(signal.symbol, 0) + signal.quantity
            )
            self.current_capital -= signal.price * signal.quantity
        else:
            self.positions[signal.symbol] = (
                self.positions.get(signal.symbol, 0) - signal.quantity
            )
            self.current_capital += signal.price * signal.quantity

        self.trades_simulated.append(trade)

    def _create_result(self) -> SandboxResult:
        """Create result from session data."""
        execution_time = 0.0
        if self._start_time:
            execution_time = (datetime.now() - self._start_time).total_seconds()

        profit_loss = self.current_capital - self.initial_capital

        return SandboxResult(
            strategy_name=self.strategy.name,
            mode=self.mode,
            signals=self.signals_generated,
            simulated_trades=self.trades_simulated,
            profit_loss=profit_loss,
            execution_time=execution_time,
            success=True,
        )

    def stop(self) -> SandboxResult:
        """Stop the session."""
        self._running = False
        self._stopped = True
        return self._create_result()

    def get_status(self) -> Dict:
        """Get current session status."""
        execution_time = 0.0
        if self._start_time:
            execution_time = (datetime.now() - self._start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "strategy_name": self.strategy.name,
            "mode": self.mode.value,
            "running": self._running,
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "profit_loss": self.current_capital - self.initial_capital,
            "signal_count": len(self.signals_generated),
            "trade_count": len(self.trades_simulated),
            "positions": dict(self.positions),
            "execution_time": execution_time,
        }
