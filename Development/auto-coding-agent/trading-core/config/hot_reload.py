"""
Configuration Hot Reload Manager

Enables dynamic reloading of configuration at runtime.
"""

import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger
from pydantic import BaseModel, ValidationError
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config.settings import get_settings


@dataclass
class ConfigVersion:
    """Configuration version information"""
    version_id: str
    config_type: str
    file_path: str
    file_hash: str
    applied_at: str
    changes: Dict[str, Any]
    rollback_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfigChangeResult:
    """Result of a configuration change"""
    success: bool
    config_type: str
    old_version: Optional[str]
    new_version: str
    message: str
    changes: Dict[str, Any]
    error: Optional[str] = None
    rollback_performed: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ConfigValidator:
    """Validates configuration changes"""

    def __init__(self, schema_path: str = "config/schemas"):
        self.schema_path = Path(schema_path)
        self.schema_path.mkdir(parents=True, exist_ok=True)

    def validate(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration data

        Args:
            config_type: Type of configuration
            config_data: Configuration data to validate

        Returns:
            True if valid
        """
        try:
            # Check required fields based on config type
            if config_type == "general":
                required_fields = ["app_name", "log_level"]
                for field in required_fields:
                    if field not in config_data:
                        logger.error(f"Missing required field: {field}")
                        return False

            elif config_type == "agent":
                required_fields = ["USE_AGENT_ARCHITECTURE"]
                for field in required_fields:
                    if field not in config_data:
                        logger.error(f"Missing required field: {field}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for config files"""

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self._debounce_timers: Dict[str, float] = {}
        self._debounce_delay = 2.0  # seconds

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = str(event.src_path)

        # Only watch config files
        if not any(file_path.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml']):
            return

        # Debounce
        now = asyncio.get_event_loop().time()
        last_time = self._debounce_timers.get(file_path, 0)

        if now - last_time < self._debounce_delay:
            return

        self._debounce_timers[file_path] = now

        logger.info(f"Config file modified: {file_path}")
        self.callback(file_path)


class ConfigHotReloadManager:
    """
    Manages hot reloading of configuration
    """

    def __init__(
        self,
        config_dir: str = "config",
        auto_reload: bool = True,
    ):
        """
        Initialize config hot reload manager

        Args:
            config_dir: Directory containing config files
            auto_reload: Whether to automatically reload on file changes
        """
        self.config_dir = Path(config_dir)
        self.auto_reload = auto_reload

        # Config versions and history
        self._config_versions: Dict[str, List[ConfigVersion]] = {}
        self._active_versions: Dict[str, str] = {}

        # Current configs
        self._current_configs: Dict[str, Dict[str, Any]] = {}

        # File watcher
        self._observer: Optional[Observer] = None
        self._watcher: Optional[ConfigFileWatcher] = None

        # Validators
        self._validator = ConfigValidator()

        # Change callbacks
        self._callbacks: List[Callable[[str, ConfigChangeResult], None]] = []

        # Change history
        self._change_history: List[ConfigChangeResult] = []

        # Initialize
        self._load_all_configs()

        logger.info(
            f"ConfigHotReloadManager initialized "
            f"(auto_reload={auto_reload}, dir={config_dir})"
        )

    def _load_all_configs(self) -> None:
        """Load all configuration files"""
        config_files = {
            ".env": "general",
            "settings.json": "general",
            "settings.yaml": "general",
            "settings.yml": "general",
        }

        for file_name, config_type in config_files.items():
            file_path = self.config_dir / file_name
            if file_path.exists():
                try:
                    self._load_config_file(str(file_path), config_type)
                except Exception as e:
                    logger.warning(f"Failed to load config {file_name}: {e}")

    def _load_config_file(self, file_path: str, config_type: str) -> Dict[str, Any]:
        """Load configuration from file"""
        file_path = Path(file_path)

        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                config_data = json.load(f)
        elif file_path.suffix in ['.yaml', '.yml']:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif file_path.suffix == '.toml':
            # TOML loading would require toml library
            logger.warning(f"TOML config not supported yet: {file_path}")
            return {}
        else:
            logger.warning(f"Unsupported config format: {file_path.suffix}")
            return {}

        # Store in current configs
        self._current_configs[config_type] = config_data

        return config_data

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def register_callback(self, callback: Callable[[str, ConfigChangeResult], None]) -> None:
        """Register callback for config changes"""
        self._callbacks.append(callback)

    def start_watching(self) -> None:
        """Start watching config files"""
        if not self.auto_reload:
            logger.info("Auto-reload disabled, not starting file watcher")
            return

        if self._observer is not None:
            logger.warning("File watcher already running")
            return

        try:
            self._watcher = ConfigFileWatcher(self._on_file_modified)
            self._observer = Observer()
            self._observer.schedule(
                self._watcher,
                path=str(self.config_dir),
                recursive=False
            )
            self._observer.start()
            logger.info(f"Started watching config files in {self.config_dir}")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")

    def stop_watching(self) -> None:
        """Stop watching config files"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching config files")

    def _on_file_modified(self, file_path: str) -> None:
        """Handle file modification"""
        try:
            # Determine config type from file name
            file_name = Path(file_path).name

            if file_name in ['.env', 'settings.json', 'settings.yaml', 'settings.yml']:
                config_type = "general"
            else:
                logger.warning(f"Unknown config file: {file_path}")
                return

            # Reload config
            result = asyncio.create_task(self.reload_config(config_type, file_path))

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(config_type, result)
                except Exception as e:
                    logger.error(f"Error in config change callback: {e}")

        except Exception as e:
            logger.error(f"Error handling file modification: {e}")

    async def reload_config(
        self,
        config_type: str,
        file_path: Optional[str] = None,
    ) -> ConfigChangeResult:
        """
        Reload configuration

        Args:
            config_type: Type of configuration
            file_path: Optional file path (auto-detected if not provided)

        Returns:
            ConfigChangeResult
        """
        old_version = self._active_versions.get(config_type)
        new_version_id = f"{config_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # Determine file path
            if not file_path:
                file_path = self._find_config_file(config_type)

            if not file_path or not Path(file_path).exists():
                return ConfigChangeResult(
                    success=False,
                    config_type=config_type,
                    old_version=old_version,
                    new_version=new_version_id,
                    message=f"Config file not found for: {config_type}",
                    error="File not found"
                )

            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)

            # Load new config
            old_config = self._current_configs.get(config_type, {})
            new_config = self._load_config_file(file_path, config_type)

            # Validate new config
            if not self._validator.validate(config_type, new_config):
                return ConfigChangeResult(
                    success=False,
                    config_type=config_type,
                    old_version=old_version,
                    new_version=new_version_id,
                    message="Config validation failed",
                    error="Validation failed"
                )

            # Detect changes
            changes = self._detect_changes(old_config, new_config)

            if not changes:
                return ConfigChangeResult(
                    success=True,
                    config_type=config_type,
                    old_version=old_version,
                    new_version=old_version or new_version_id,
                    message="Config unchanged, skipping reload",
                    changes={},
                )

            # Save rollback data
            rollback_data = old_config.copy()

            # Apply new config
            await self._apply_config(config_type, new_config)

            # Create version record
            version = ConfigVersion(
                version_id=new_version_id,
                config_type=config_type,
                file_path=file_path,
                file_hash=file_hash,
                applied_at=datetime.now().isoformat(),
                changes=changes,
                rollback_data=rollback_data,
            )

            # Store version
            if config_type not in self._config_versions:
                self._config_versions[config_type] = []

            self._config_versions[config_type].append(version)
            self._active_versions[config_type] = new_version_id

            result = ConfigChangeResult(
                success=True,
                config_type=config_type,
                old_version=old_version,
                new_version=new_version_id,
                message=f"Successfully reloaded config: {config_type}",
                changes=changes,
            )

            logger.info(f"Reloaded config {config_type}: {len(changes)} changes")

        except Exception as e:
            error_msg = f"Failed to reload config: {str(e)}"
            logger.error(error_msg)

            # Attempt rollback
            rollback_success = await self._rollback_config(config_type, old_version)

            result = ConfigChangeResult(
                success=False,
                config_type=config_type,
                old_version=old_version,
                new_version=new_version_id,
                message=error_msg,
                error=str(e),
                rollback_performed=rollback_success,
            )

        # Store in history
        self._change_history.append(result)

        if len(self._change_history) > 100:
            self._change_history = self._change_history[-100:]

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(config_type, result)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")

        return result

    def _find_config_file(self, config_type: str) -> Optional[str]:
        """Find config file by type"""
        possible_files = [
            self.config_dir / "settings.json",
            self.config_dir / "settings.yaml",
            self.config_dir / "settings.yml",
            self.config_dir / ".env",
        ]

        for file_path in possible_files:
            if file_path.exists():
                return str(file_path)

        return None

    def _detect_changes(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect changes between configs"""
        changes = {}

        all_keys = set(old_config.keys()) | set(new_config.keys())

        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value,
                }

        return changes

    async def _apply_config(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """Apply configuration changes"""
        # Update settings module
        from config import settings

        # Update settings values
        for key, value in config_data.items():
            if hasattr(settings, key):
                try:
                    setattr(settings, key, value)
                    logger.debug(f"Updated config {key} = {value}")
                except Exception as e:
                    logger.warning(f"Failed to set config {key}: {e}")

    async def _rollback_config(self, config_type: str, version_id: str) -> bool:
        """Rollback configuration to previous version"""
        if not version_id:
            return False

        try:
            version_info = None
            for v in self._config_versions.get(config_type, []):
                if v.version_id == version_id:
                    version_info = v
                    break

            if not version_info:
                logger.error(f"Version not found: {version_id}")
                return False

            # Apply rollback data
            await self._apply_config(config_type, version_info.rollback_data)

            logger.info(f"Rolled back config {config_type} to {version_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback config {config_type}: {e}")
            return False

    def get_config_versions(self, config_type: str) -> List[ConfigVersion]:
        """Get all versions of a config"""
        return self._config_versions.get(config_type, [])

    def get_current_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Get current configuration"""
        return self._current_configs.get(config_type)

    async def update_config(
        self,
        config_type: str,
        updates: Dict[str, Any],
    ) -> ConfigChangeResult:
        """
        Update configuration programmatically

        Args:
            config_type: Type of configuration
            updates: Key-value pairs to update

        Returns:
            ConfigChangeResult
        """
        old_config = self._current_configs.get(config_type, {}).copy()
        new_config = old_config.copy()
        new_config.update(updates)

        # Validate
        if not self._validator.validate(config_type, new_config):
            return ConfigChangeResult(
                success=False,
                config_type=config_type,
                old_version=self._active_versions.get(config_type),
                new_version="",
                message="Config validation failed",
                error="Validation failed"
            )

        # Detect changes
        changes = {k: {"old": old_config.get(k), "new": v} for k, v in updates.items()}

        try:
            # Apply changes
            await self._apply_config(config_type, new_config)

            # Update current config
            self._current_configs[config_type] = new_config

            # Note: For programmatic updates, we don't create a new version
            # unless we want to persist to file

            result = ConfigChangeResult(
                success=True,
                config_type=config_type,
                old_version=self._active_versions.get(config_type),
                new_version=self._active_versions.get(config_type, ""),
                message=f"Updated {len(updates)} config values",
                changes=changes,
            )

        except Exception as e:
            result = ConfigChangeResult(
                success=False,
                config_type=config_type,
                old_version=self._active_versions.get(config_type),
                new_version="",
                message=f"Failed to update config: {str(e)}",
                error=str(e),
            )

        return result

    def get_change_history(
        self,
        config_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[ConfigChangeResult]:
        """Get change history"""
        history = self._change_history[-limit:]

        if config_type:
            history = [r for r in history if r.config_type == config_type]

        return history

    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "auto_reload": self.auto_reload,
            "watching": self._observer is not None,
            "config_dir": str(self.config_dir),
            "total_configs": len(self._current_configs),
            "active_versions": self._active_versions,
            "change_count": len(self._change_history),
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_manager: Optional[ConfigHotReloadManager] = None


def get_config_reload_manager() -> Optional[ConfigHotReloadManager]:
    """Get global config reload manager"""
    return _manager


def init_config_reload_manager(
    config_dir: str = "config",
    auto_reload: bool = True,
) -> ConfigHotReloadManager:
    """Initialize global config reload manager"""
    global _manager
    _manager = ConfigHotReloadManager(
        config_dir=config_dir,
        auto_reload=auto_reload,
    )
    return _manager
