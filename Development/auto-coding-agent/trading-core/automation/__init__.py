"""
自动化交易模块
Automation Trading Module for Tonghuashun
"""

from .window import (
    find_tonghuashun_window,
    find_all_windows,
    bring_window_to_front,
    screenshot_window,
    screenshot_region,
    screenshot_screen,
    save_screenshot,
    TemplateMatcher,
    CoordinateManager,
    matcher,
    coord_manager,
    IS_WINDOWS,
    IS_MACOS,
    IS_LINUX,
)

from .trader import (
    THSTrader,
    OrderSide,
    OrderType,
    TradingError,
    TradingResult,
    trader,
)

from .screenshot import (
    ScreenshotManager,
    screenshot_manager,
)

__all__ = [
    # Window module
    'find_tonghuashun_window',
    'find_all_windows',
    'bring_window_to_front',
    'screenshot_window',
    'screenshot_region',
    'screenshot_screen',
    'save_screenshot',
    'TemplateMatcher',
    'CoordinateManager',
    'matcher',
    'coord_manager',
    'IS_WINDOWS',
    'IS_MACOS',
    'IS_LINUX',
    # Trader module
    'THSTrader',
    'OrderSide',
    'OrderType',
    'TradingError',
    'TradingResult',
    'trader',
    # Screenshot module
    'ScreenshotManager',
    'screenshot_manager',
]
