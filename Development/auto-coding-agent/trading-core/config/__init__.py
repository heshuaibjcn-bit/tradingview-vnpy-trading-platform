"""StockAutoTrader Configuration Module"""

from .settings import settings, get_settings, Settings

__all__ = ["settings", "get_settings", "Settings"]

# Hot reload support
from .hot_reload import (
    ConfigHotReloadManager,
    ConfigVersion,
    ConfigChangeResult,
    get_config_reload_manager,
    init_config_reload_manager,
)

__all__.extend([
    "ConfigHotReloadManager",
    "ConfigVersion",
    "ConfigChangeResult",
    "get_config_reload_manager",
    "init_config_reload_manager",
])
