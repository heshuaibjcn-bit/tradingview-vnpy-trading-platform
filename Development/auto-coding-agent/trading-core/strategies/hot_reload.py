"""
Strategy Hot Reload Manager

Enables dynamic loading and reloading of trading strategies at runtime.
"""

import importlib
import sys
import inspect
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from strategies.base import Strategy
from strategies.engine import StrategyEngine


@dataclass
class StrategyVersion:
    """Strategy version information"""
    version_id: str
    file_path: str
    file_hash: str
    loaded_at: str
    strategy_class: str
    is_active: bool
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReloadResult:
    """Result of a strategy reload operation"""
    success: bool
    strategy_id: str
    old_version: Optional[str]
    new_version: str
    message: str
    error: Optional[str] = None
    rollback_performed: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class StrategyFileWatcher(FileSystemEventHandler):
    """File system watcher for strategy files"""

    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize file watcher

        Args:
            callback: Function to call when file is modified
        """
        self.callback = callback
        self._debounce timers: Dict[str, float] = {}
        self._debounce_delay = 1.0  # seconds

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event"""
        if event.is_directory:
            return

        # Only watch .py files
        if not event.src_path.endswith('.py'):
            return

        file_path = str(event.src_path)

        # Debounce rapid file changes
        now = asyncio.get_event_loop().time()
        last_time = self._debounce_timers.get(file_path, 0)

        if now - last_time < self._debounce_delay:
            return

        self._debounce_timers[file_path] = now

        logger.info(f"Strategy file modified: {file_path}")
        self.callback(file_path)


class StrategyHotReloadManager:
    """
    Manages hot reloading of trading strategies
    """

    def __init__(
        self,
        strategy_engine: StrategyEngine,
        strategies_dir: str = "strategies",
        auto_reload: bool = True,
    ):
        """
        Initialize strategy hot reload manager

        Args:
            strategy_engine: StrategyEngine instance
            strategies_dir: Directory containing strategy files
            auto_reload: Whether to automatically reload on file changes
        """
        self.strategy_engine = strategy_engine
        self.strategies_dir = Path(strategies_dir)
        self.auto_reload = auto_reload

        # Strategy versions
        self._strategy_versions: Dict[str, List[StrategyVersion]] = {}
        self._active_versions: Dict[str, str] = {}

        # File watcher
        self._observer: Optional[Observer] = None
        self._watcher: Optional[StrategyFileWatcher] = None

        # Reload callbacks
        self._callbacks: List[Callable[[str, ReloadResult], None]] = []

        # Reload history
        self._reload_history: List[ReloadResult] = []

        logger.info(
            f"StrategyHotReloadManager initialized "
            f"(auto_reload={auto_reload}, dir={strategies_dir})"
        )

    def register_callback(self, callback: Callable[[str, ReloadResult], None]) -> None:
        """
        Register a callback for reload events

        Args:
            callback: Function to call with strategy_id and ReloadResult
        """
        self._callbacks.append(callback)

    def start_watching(self) -> None:
        """Start watching strategy files for changes"""
        if not self.auto_reload:
            logger.info("Auto-reload disabled, not starting file watcher")
            return

        if self._observer is not None:
            logger.warning("File watcher already running")
            return

        try:
            self._watcher = StrategyFileWatcher(self._on_file_modified)
            self._observer = Observer()
            self._observer.schedule(
                self._watcher,
                path=str(self.strategies_dir),
                recursive=True
            )
            self._observer.start()
            logger.info(f"Started watching strategy files in {self.strategies_dir}")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")

    def stop_watching(self) -> None:
        """Stop watching strategy files"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching strategy files")

    def _on_file_modified(self, file_path: str) -> None:
        """Handle file modification event"""
        try:
            # Find strategy ID from file path
            strategy_id = self._find_strategy_id_by_file(file_path)

            if strategy_id:
                logger.info(f"Auto-reloading strategy: {strategy_id}")
                result = asyncio.create_task(self.reload_strategy(strategy_id))

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(strategy_id, result)
                    except Exception as e:
                        logger.error(f"Error in reload callback: {e}")
        except Exception as e:
            logger.error(f"Error handling file modification: {e}")

    def _find_strategy_id_by_file(self, file_path: str) -> Optional[str]:
        """Find strategy ID by file path"""
        file_path = Path(file_path).relative_to(self.strategies_dir)

        # Get all loaded strategies
        strategies = self.strategy_engine.list_strategies()

        for strategy_id, strategy_info in strategies.items():
            # Check if file path matches strategy module
            if strategy_id in str(file_path):
                return strategy_id

        return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def _load_strategy_module(self, file_path: str):
        """Load strategy module from file"""
        # Convert file path to module path
        file_path = Path(file_path).relative_to(Path.cwd())

        module_name = str(file_path.with_suffix('')).replace('/', '.')

        # Remove leading dot if present
        if module_name.startswith('.'):
            module_name = module_name[1:]

        # Import or reload module
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)

        return module

    def _extract_strategy_class(self, module, strategy_id: str):
        """Extract strategy class from module"""
        # Find Strategy subclass
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Strategy) and obj != Strategy:
                # Check if class name matches strategy_id
                if strategy_id.lower() in name.lower():
                    return obj

        # If no match, return first Strategy subclass
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Strategy) and obj != Strategy:
                return obj

        raise ValueError(f"No Strategy class found in module {module.__name__}")

    def _save_strategy_state(self, strategy_id: str) -> Dict[str, Any]:
        """Save current strategy state before reload"""
        strategy = self.strategy_engine.get_strategy(strategy_id)

        if not strategy:
            return {}

        # Extract state
        state = {
            'parameters': getattr(strategy, 'parameters', {}),
            'position': getattr(strategy, 'position', 0),
            'signals': getattr(strategy, 'signals', []),
            'last_signal_time': getattr(strategy, 'last_signal_time', None),
        }

        return state

    def _restore_strategy_state(
        self,
        strategy: Strategy,
        state: Dict[str, Any],
    ) -> None:
        """Restore strategy state after reload"""
        for key, value in state.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)

    async def reload_strategy(
        self,
        strategy_id: str,
        force: bool = False,
    ) -> ReloadResult:
        """
        Reload a strategy

        Args:
            strategy_id: Strategy ID to reload
            force: Force reload even if file hasn't changed

        Returns:
            ReloadResult
        """
        old_version = self._active_versions.get(strategy_id)
        new_version_id = f"{strategy_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # Get current strategy state
            old_state = self._save_strategy_state(strategy_id)

            # Find strategy file
            strategy_info = self.strategy_engine.get_strategy_info(strategy_id)
            if not strategy_info:
                return ReloadResult(
                    success=False,
                    strategy_id=strategy_id,
                    old_version=old_version,
                    new_version=new_version_id,
                    message=f"Strategy not found: {strategy_id}",
                    error="Strategy not found"
                )

            # Get strategy file path
            strategy_class_name = strategy_info.get('class_name', '')
            possible_files = list(self.strategies_dir.rglob(f"{strategy_id.lower()}.py"))

            if not possible_files:
                return ReloadResult(
                    success=False,
                    strategy_id=strategy_id,
                    old_version=old_version,
                    new_version=new_version_id,
                    message=f"Strategy file not found for: {strategy_id}",
                    error="File not found"
                )

            strategy_file = possible_files[0]

            # Calculate file hash
            file_hash = self._calculate_file_hash(str(strategy_file))

            # Check if file has changed
            if not force and old_version:
                old_version_info = self._get_version_info(old_version)
                if old_version_info and old_version_info.file_hash == file_hash:
                    return ReloadResult(
                        success=True,
                        strategy_id=strategy_id,
                        old_version=old_version,
                        new_version=old_version,
                        message="Strategy file unchanged, skipping reload",
                    )

            # Load new strategy module
            module = self._load_strategy_module(str(strategy_file))
            strategy_class = self._extract_strategy_class(module, strategy_id)

            # Create new strategy instance
            new_strategy = strategy_class()

            # Restore state
            self._restore_strategy_state(new_strategy, old_state)

            # Update strategy in engine
            await self.strategy_engine.update_strategy(strategy_id, new_strategy)

            # Create version record
            version = StrategyVersion(
                version_id=new_version_id,
                file_path=str(strategy_file),
                file_hash=file_hash,
                loaded_at=datetime.now().isoformat(),
                strategy_class=strategy_class.__name__,
                is_active=True,
                parameters=getattr(new_strategy, 'parameters', {}),
            )

            # Store version
            if strategy_id not in self._strategy_versions:
                self._strategy_versions[strategy_id] = []

            # Deactivate old version
            if old_version:
                for v in self._strategy_versions[strategy_id]:
                    if v.version_id == old_version:
                        v.is_active = False

            self._strategy_versions[strategy_id].append(version)
            self._active_versions[strategy_id] = new_version_id

            result = ReloadResult(
                success=True,
                strategy_id=strategy_id,
                old_version=old_version,
                new_version=new_version_id,
                message=f"Successfully reloaded strategy: {strategy_id}",
            )

            logger.info(f"Reloaded strategy {strategy_id}: {old_version} -> {new_version_id}")

        except Exception as e:
            error_msg = f"Failed to reload strategy: {str(e)}"
            logger.error(error_msg)

            # Attempt rollback
            rollback_success = await self._rollback_strategy(strategy_id, old_version)

            result = ReloadResult(
                success=False,
                strategy_id=strategy_id,
                old_version=old_version,
                new_version=new_version_id,
                message=error_msg,
                error=str(e),
                rollback_performed=rollback_success,
            )

        # Store in history
        self._reload_history.append(result)

        # Trim history
        if len(self._reload_history) > 100:
            self._reload_history = self._reload_history[-100:]

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(strategy_id, result)
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")

        return result

    async def _rollback_strategy(self, strategy_id: str, version_id: str) -> bool:
        """
        Rollback strategy to previous version

        Args:
            strategy_id: Strategy ID
            version_id: Version ID to rollback to

        Returns:
            True if successful
        """
        if not version_id:
            logger.warning(f"Cannot rollback {strategy_id}: no previous version")
            return False

        try:
            version_info = self._get_version_info(version_id)

            if not version_info:
                logger.error(f"Version not found: {version_id}")
                return False

            # Load old version
            module = self._load_strategy_module(version_info.file_path)
            strategy_class = getattr(module, version_info.strategy_class)
            old_strategy = strategy_class()

            # Restore parameters
            if version_info.parameters:
                for key, value in version_info.parameters.items():
                    if hasattr(old_strategy, key):
                        setattr(old_strategy, key, value)

            # Update strategy in engine
            await self.strategy_engine.update_strategy(strategy_id, old_strategy)

            logger.info(f"Rolled back strategy {strategy_id} to {version_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback strategy {strategy_id}: {e}")
            return False

    def _get_version_info(self, version_id: str) -> Optional[StrategyVersion]:
        """Get version information by ID"""
        for versions in self._strategy_versions.values():
            for v in versions:
                if v.version_id == version_id:
                    return v
        return None

    def get_strategy_versions(self, strategy_id: str) -> List[StrategyVersion]:
        """Get all versions of a strategy"""
        return self._strategy_versions.get(strategy_id, [])

    def get_reload_history(
        self,
        strategy_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ReloadResult]:
        """
        Get reload history

        Args:
            strategy_id: Filter by strategy ID
            limit: Maximum results

        Returns:
            List of ReloadResult
        """
        history = self._reload_history[-limit:]

        if strategy_id:
            history = [r for r in history if r.strategy_id == strategy_id]

        return history

    def get_active_version(self, strategy_id: str) -> Optional[str]:
        """Get active version ID for a strategy"""
        return self._active_versions.get(strategy_id)

    async def rollback_to_version(
        self,
        strategy_id: str,
        version_id: str,
    ) -> ReloadResult:
        """
        Rollback strategy to specific version

        Args:
            strategy_id: Strategy ID
            version_id: Version ID to rollback to

        Returns:
            ReloadResult
        """
        old_version = self._active_versions.get(strategy_id)

        success = await self._rollback_strategy(strategy_id, version_id)

        if success:
            # Update active version
            self._active_versions[strategy_id] = version_id

            result = ReloadResult(
                success=True,
                strategy_id=strategy_id,
                old_version=old_version,
                new_version=version_id,
                message=f"Rolled back to version: {version_id}",
                rollback_performed=True,
            )
        else:
            result = ReloadResult(
                success=False,
                strategy_id=strategy_id,
                old_version=old_version,
                new_version=old_version,
                message="Rollback failed",
                error="Failed to rollback strategy",
            )

        self._reload_history.append(result)
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get hot reload manager status"""
        return {
            "auto_reload": self.auto_reload,
            "watching": self._observer is not None,
            "strategies_dir": str(self.strategies_dir),
            "total_strategies": len(self._strategy_versions),
            "active_versions": self._active_versions,
            "reload_count": len(self._reload_history),
            "timestamp": datetime.now().isoformat(),
        }


# Global hot reload manager instance
_manager: Optional[StrategyHotReloadManager] = None


def get_hot_reload_manager() -> Optional[StrategyHotReloadManager]:
    """Get global hot reload manager instance"""
    return _manager


def init_hot_reload_manager(
    strategy_engine: StrategyEngine,
    strategies_dir: str = "strategies",
    auto_reload: bool = True,
) -> StrategyHotReloadManager:
    """
    Initialize global hot reload manager

    Args:
        strategy_engine: StrategyEngine instance
        strategies_dir: Directory containing strategies
        auto_reload: Enable automatic reloading

    Returns:
        StrategyHotReloadManager instance
    """
    global _manager
    _manager = StrategyHotReloadManager(
        strategy_engine=strategy_engine,
        strategies_dir=strategies_dir,
        auto_reload=auto_reload,
    )
    return _manager
